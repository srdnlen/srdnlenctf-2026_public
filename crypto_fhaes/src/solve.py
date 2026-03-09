from sage.all import BooleanPolynomialRing, Sequence
from srdnlengarble import BinaryCircuit, BinaryGate, Evaluator, PwnToolsChannel, Receiver
from pwn import process
import os, common, json, collections, itertools


name = "custom_circuit"
custom_circuit = []
for i in range(128):
    gate = {
        'type': 'AND',
        'inputs': [f'x{i}'] * 2,
        'output': f'y{i}'
    }
    custom_circuit.append(gate)

func, num_args = common.circuits[name]
assert num_args == 1
binary_circuit, input_info = func(custom_circuit)
assert isinstance(binary_circuit, BinaryCircuit), "Invalid circuit returned"
garbler_inputs = input_info['garbler']
assert len(garbler_inputs) == 1
evaluator_inputs = input_info['evaluator']
assert len(evaluator_inputs) == 1


def evaluate_and_gate(evaluator: "MyEvaluator", A, B, gate0, gate1, gate_num):
    g = gate_num.to_bytes(16, 'big')
        
    hashA, hashB = evaluator.hash_wires([A, B], g)

    L = hashA if (A & 1) == 0 else hashA ^ gate0
    R = hashB if (B & 1) == 0 else hashB ^ gate1

    return L ^ R ^ (A * (B & 1))


class MyEvaluator(Evaluator):
    def __init__(self, channel):
        super().__init__(channel)
        self.and_gates_data = []
    
    def and_gate(self, x, y):
        gate0 = self.channel.read_wire()
        gate1 = self.channel.read_wire()
        z = evaluate_and_gate(self, x, y, gate0, gate1, self.current_gate())
        self.and_gates_data.append((x, y, gate0, gate1, z))
        return z


io = process(['python3', 'server.py'])

io.sendlineafter(
    b'Enter circuit name and args (hex encoded JSON): ',
    (name + " " + json.dumps(custom_circuit).encode().hex()).encode()
)

channel = PwnToolsChannel(io)
evaluator = MyEvaluator(channel)
assert garbler_inputs.get('key', 0) == 128
key_evaluator = channel.read_wires(128)
# OT phase
receiver = Receiver(channel)
inp_name, inp_size = next(iter(evaluator_inputs.items()))
assert inp_size % 8 == 0, "input size must be a multiple of 8"
io.recvline_contains(
    f"Sending evaluator input wires for {inp_name} ({inp_size} bits)...".encode()
)
choices = common.bytes_to_bits(os.urandom(inp_size // 8))
evaluator_wires = receiver.receive(choices)
# Garbling/evaluation phase
io.recvline_contains(b"Evaluating circuit...")
out_bits = binary_circuit.eval(evaluator, key_evaluator, evaluator_wires)
assert out_bits is not None
assert common.bits_to_bytes(out_bits) == common.bits_to_bytes(choices)

# recover delta from AND gates with equal inputs
cnt = collections.Counter()
for i, (x, y, gate0, gate1, z) in enumerate(evaluator.and_gates_data):
    A, B = x, y
    if A != B:
        continue
    cnt[A ^ gate0 ^ gate1] += 1
for delta, frequency in cnt.most_common():
    if delta != 0:
        print(f"Found delta: {f'{delta:032x}'} with frequency {frequency}")
        break
else:
    raise ValueError("Failed to recover delta")

# recover key bits
B = BooleanPolynomialRing(128, 'k')
wire_map, value_map = dict(), dict()
for i, wire_id in enumerate(binary_circuit.garbler_inputs):
    wire_map[wire_id] = key_evaluator[i]
    value_map[wire_id] = B.gen(i)
for i, wire_id in enumerate(binary_circuit.evaluator_inputs):
    wire_map[wire_id] = evaluator_wires[i]
    value_map[wire_id] = choices[i]


def find_and_values(x, y, gate0, gate1, gate_num) -> tuple[int, int]:
    global delta, evaluator

    for a, b in itertools.product([0, 1], repeat=2):
        A = x ^ (a * delta)
        B = y ^ (b * delta)
        
        r = B & 1
        g = gate_num.to_bytes(16, 'big')

        alpha = A & 1
        X1 = A ^ (delta * alpha)

        beta = B & 1
        Y1 = B ^ (delta * beta)

        AD = A ^ delta
        BD = B ^ delta

        a_selector = A & 1
        b_selector = B & 1

        B = BD if b_selector == 0 else B
        newA = AD if a_selector == 0 else A
        idx = r if a_selector == 0 else 0

        hashA, hashB, hashX, hashY = evaluator.hash_wires([newA, B, X1, Y1], g)

        X = hashX ^ (delta * (alpha * r % 2))
        Y = hashY

        gate0_ = hashA ^ (X if idx == 0 else X ^ delta)
        gate1_ = hashB ^ (Y ^ A)

        if gate0_ == gate0 and gate1_ == gate1:
            return a, b
    raise ValueError("Failed to find AND gate input values")


and_gates_data = enumerate(evaluator.and_gates_data)
polys = []
for gate in binary_circuit.gates:
    if isinstance(gate, BinaryGate.Xor):
        a = wire_map[gate.input_left]
        b = wire_map[gate.input_right]
        c = a ^ b  # free-XOR
        wire_map[gate.output_wire] = c
        a = value_map[gate.input_left]
        b = value_map[gate.input_right]
        c = a + b
        value_map[gate.output_wire] = c
    
    elif isinstance(gate, BinaryGate.And):
        gate_num, (x, y, gate0, gate1, z) = next(and_gates_data)
        assert wire_map[gate.input_left] == x
        assert wire_map[gate.input_right] == y
        assert z == evaluate_and_gate(
            evaluator, x, y, gate0, gate1, gate_num
        )
        wire_map[gate.output_wire] = z
        a, b = find_and_values(x, y, gate0, gate1, gate_num)
        polys.append(value_map[gate.input_left] - a)
        polys.append(value_map[gate.input_right] - b)
        value_map[gate.output_wire] = a * b
    
    elif isinstance(gate, BinaryGate.Not):
        a = wire_map[gate.input_wire]
        c = a  # no-op for evaluator
        wire_map[gate.output_wire] = c
        a = value_map[gate.input_wire]
        c = a + 1
        value_map[gate.output_wire] = c
    
    elif isinstance(gate, BinaryGate.EqualityConstraint):
        lhs = wire_map.get(gate.lhs, None)
        rhs = wire_map.get(gate.rhs, None)
        if lhs is not None and rhs is not None:
            if lhs != rhs:
                raise ValueError("equality constraint violated during evaluation")
        elif lhs is not None:
            wire_map[gate.rhs] = lhs
        elif rhs is not None:
            wire_map[gate.lhs] = rhs
        else:
            raise ValueError("cannot evaluate equality constraint with unknown wires")
        lhs = value_map.get(gate.lhs, None)
        rhs = value_map.get(gate.rhs, None)
        if lhs is not None and rhs is not None:
            if lhs != rhs:
                raise ValueError("equality constraint violated during symbolic evaluation")
        elif lhs is not None:
            value_map[gate.rhs] = lhs
        elif rhs is not None:
            value_map[gate.lhs] = rhs
        else:
            raise ValueError("cannot symbolically evaluate equality constraint with unknown wires")

# solve for key bits
M, mons = Sequence(polys).coefficients_monomials(sparse=False)
K = M.right_kernel_matrix()
assert K.nrows() == 1, "Expected 1-dimensional kernel"
key_bits = list(map(int, K.row(0)[:-1]))
key = common.bits_to_bytes(key_bits)

io.sendlineafter(b'Enter circuit name and args (hex encoded JSON): ', b'')
io.sendlineafter(b'Enter your guess for the key (hex): ', key.hex().encode())

try:
    io.interactive()
except (EOFError, KeyboardInterrupt):
    pass
finally:
    io.close()
