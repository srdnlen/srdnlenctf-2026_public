from srdnlengarble import BinaryCircuit
from fhaes import FHAES

__all__ = [
    'bytes_to_bits',
    'bits_to_bytes',
    'circuits',
]

bytes_to_bits = lambda b: [(b[i // 8] >> (i % 8)) & 1 for i in range(len(b) * 8)]
bits_to_bytes = lambda b: bytes(sum(b[i * 8 + j] << j for j in range(8)) for i in range(len(b) // 8))

InputInfo = dict[str, dict[str, int]]


def encrypt() -> tuple[BinaryCircuit, InputInfo]:
    fhaes = FHAES()
    pt = fhaes.evaluator_bytes(16)
    ct = fhaes.output_bytes(16)
    for x, y in zip(fhaes.encrypt(pt), ct):
        x == y  # link encryption wires to output wires
    return fhaes.binary_circuit, {
        'garbler': {'key': 128},
        'evaluator': {'pt': 128},
    }


def decrypt() -> tuple[BinaryCircuit, InputInfo]:
    fhaes = FHAES()
    ct = fhaes.evaluator_bytes(16)
    pt = fhaes.output_bytes(16)
    for x, y in zip(fhaes.decrypt(ct), pt):
        x == y  # link decryption wires to output wires
    return fhaes.binary_circuit, {
        'garbler': {'key': 128},
        'evaluator': {'ct': 128},
    }


def add() -> tuple[BinaryCircuit, InputInfo]:
    fhaes = FHAES()
    ct0 = fhaes.evaluator_bytes(16)
    ct1 = fhaes.evaluator_bytes(16)
    ct = fhaes.output_bytes(16)
    pt0 = fhaes.decrypt(ct0)
    pt1 = fhaes.decrypt(ct1)
    pt = fhaes.add(pt0, pt1)
    for x, y in zip(fhaes.encrypt(pt), ct):
        x == y  # link encryption wires to output wires
    return fhaes.binary_circuit, {
        'garbler': {'key': 128},
        'evaluator': {'ct0': 128, 'ct1': 128},
    }


def multiply() -> tuple[BinaryCircuit, InputInfo]:
    fhaes = FHAES()
    ct0 = fhaes.evaluator_bytes(16)
    ct1 = fhaes.evaluator_bytes(16)
    ct = fhaes.output_bytes(16)
    pt0 = fhaes.decrypt(ct0)
    pt1 = fhaes.decrypt(ct1)
    pt = fhaes.multiply(pt0, pt1)
    for x, y in zip(fhaes.encrypt(pt), ct):
        x == y  # link encryption wires to output wires
    return fhaes.binary_circuit, {
        'garbler': {'key': 128},
        'evaluator': {'ct0': 128, 'ct1': 128},
    }


def custom_circuit(circuit: list[dict]) -> tuple[BinaryCircuit, InputInfo]:
    fhaes = FHAES()
    ct = fhaes.evaluator_bytes(16)
    ct_new = fhaes.output_bytes(16)
    pt = fhaes.decrypt(ct)
    pt_new = fhaes.custom_circuit(pt, circuit)
    for x, y in zip(fhaes.encrypt(pt_new), ct_new):
        x == y  # link encryption wires to output wires
    return fhaes.binary_circuit, {
        'garbler': {'key': 128},
        'evaluator': {'ct': 128},
    }


circuits = {
    'encrypt': (encrypt, 0),
    'decrypt': (decrypt, 0),
    'add': (add, 0),
    'multiply': (multiply, 0),
    'custom_circuit': (custom_circuit, 1),  # circuit passed as argument
}
