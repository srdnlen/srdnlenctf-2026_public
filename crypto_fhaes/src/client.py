from srdnlengarble import BinaryCircuit, Evaluator, PwnToolsChannel, Receiver
from pwn import remote, process, context, PwnlibException
import os, sys, common, time, json


if sys.argv[1] == 'remote':
    try:
        host = sys.argv[2]
        port = int(sys.argv[3])
        context.log_level = 'error'  # suppress pwnlib info messages
        io = remote(host, port)
    except PwnlibException:
        print("Failed to connect to remote server")
        sys.exit(1)
else:
    try:
        context.log_level = 'error'  # suppress pwnlib info messages
        io = process(['python3', 'server.py'])
    except PwnlibException:
        print("Failed to start local process")
        sys.exit(1)

try:
    print("Available circuits:")
    for name, (func, num_args) in common.circuits.items():
        print(f"- {name} (args: {num_args})")
    print()

    while True:  # if you think you can do it adaptively be my guest
        name, *args = input("Enter circuit name and args (hex encoded JSON): ").strip().split(" ")
        if not name:  # allow early exit
            io.sendlineafter(b'Enter circuit name and args (hex encoded JSON): ', b'')
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
        # Reply to server prompt
        io.sendlineafter(
            b'Enter circuit name and args (hex encoded JSON): ',
            f"{name} {' '.join(args)}".encode()
        )

        channel = PwnToolsChannel(io)
        evaluator = Evaluator(channel)
        assert garbler_inputs.get('key', 0) == 128
        key_evaluator = channel.read_wires(128)
        # OT phase
        receiver = Receiver(channel)
        evaluator_wires = []
        for inp_name, inp_size in evaluator_inputs.items():
            print(f"Receiving evaluator input wires for {inp_name} ({inp_size} bits)...")
            io.recvline_contains(
                f"Sending evaluator input wires for {inp_name} ({inp_size} bits)...".encode()
            )
            assert inp_size % 8 == 0, "Input size must be a multiple of 8"
            method, *data = input(
                f"Enter method and data for {inp_name} (e.g., 'random', 'bytes <data>', 'hex <data>'): "
            ).split(" ", 1)
            if method == 'random':
                inp_bytes = os.urandom(inp_size // 8)
            elif method == 'bytes':
                if len(data) == 0:
                    raise ValueError("Missing data for 'bytes' method")
                data = data.pop()
                if len(data) != inp_size // 8:
                    raise ValueError(f"Data length must be {inp_size // 8} bytes")
                inp_bytes = data.encode()
            elif method == 'hex':
                if len(data) == 0:
                    raise ValueError("Missing data for 'hex' method")
                data = data.pop()
                if len(data) != (inp_size // 8) * 2:
                    raise ValueError(f"Data length must be {(inp_size // 8) * 2} hex characters")
                inp_bytes = bytes.fromhex(data)
            else:
                raise ValueError("Invalid input method or missing data")
            assert len(inp_bytes) == inp_size // 8, f"Input data must be {inp_size // 8} bytes"
            choices = common.bytes_to_bits(inp_bytes)
            wires = receiver.receive(choices)
            evaluator_wires.extend(wires)
        # Garbling/evaluation phase
        print("Evaluating circuit...")
        start = time.time()
        io.recvline_contains(b"Evaluating circuit...")
        out_bits = binary_circuit.eval(evaluator, key_evaluator, evaluator_wires)
        assert out_bits is not None
        end = time.time()
        print(f"Evaluation took {end - start:.2f} seconds")
        out = common.bits_to_bytes(out_bits)
        print(f"Output (hex): {out.hex()}")

    guess = input("Enter your guess for the key (hex): ").strip()
    io.sendlineafter(b'Enter your guess for the key (hex): ', guess.encode())
    io.interactive()
except (EOFError, KeyboardInterrupt):
    print()
except Exception as e:
    print(f"Error: {e}")
finally:
    io.close()
