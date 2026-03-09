from srdnlengarble import BinaryCircuit, Garbler, StdIOChannel, Sender
import os, json, common

key = os.urandom(16)

print("Available circuits:")
for name, (func, num_args) in common.circuits.items():
    print(f"- {name} (args: {num_args})")
print()

while True:  # if you think you can do it adaptively be my guest
    name, *args = input("Enter circuit name and args (hex encoded JSON): ").strip().split(" ")
    if not name:  # allow early exit
        break
    if name not in common.circuits:
        raise ValueError("Unknown circuit name")
    func, num_args = common.circuits[name]
    if len(args) != num_args:
        raise ValueError(f"{name} requires {num_args} arguments")
    binary_circuit, input_info = func(*map(lambda x: json.loads(bytes.fromhex(x)), args))
    assert isinstance(binary_circuit, BinaryCircuit), "Invalid circuit returned"
    garbler_inputs = input_info['garbler']
    evaluator_inputs = input_info['evaluator']

    channel = StdIOChannel()
    garbler = Garbler(channel)
    assert garbler_inputs.get('key', 0) == 128
    key_garbler, key_evaluator = garbler.encode_wires(common.bytes_to_bits(key))
    channel.send_wires(key_evaluator)
    # OT phase
    sender = Sender(channel)
    evaluator_wires = []
    for inp_name, inp_size in evaluator_inputs.items():
        print(f"Sending evaluator input wires for {inp_name} ({inp_size} bits)...")
        wires = garbler.evaluator_inputs(inp_size)
        evaluator_wires.extend([zero for zero, _ in wires])
        sender.send(wires)
    # Garbling/evaluation phase
    print("Evaluating circuit...")
    binary_circuit.eval(garbler, key_garbler, evaluator_wires)

guess = bytes.fromhex(input("Enter your guess for the key (hex): ").strip())
if guess == key:
    print(f"Correct! Here is your flag: {os.getenv('FLAG', 'srdnlen{this_is_a_fake_flag}')}")
else:
    print("Incorrect key guess. Better luck next time!")
