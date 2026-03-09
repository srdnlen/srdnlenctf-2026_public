from srdnlengarble import Garbler, InMemoryChannel

channel = InMemoryChannel()
garbler = Garbler(channel)
# Test AND gate garbling with identical inputs
A, AD = garbler.encode_wire(1)
B, BD = A, AD
gate0, gate1, Z = garbler._Garbler__garble_and_gate(A, B)
print(f"{A = }")
print(f"{AD = }")
print(f"{gate0 ^ gate1 = }")
assert garbler.delta in (A ^ gate0 ^ gate1, AD ^ gate0 ^ gate1)
