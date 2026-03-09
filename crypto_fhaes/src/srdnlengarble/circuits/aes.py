from .optimized_sbox import OptimizedSBox

__all__ = ['AES']


# Based on https://cryptohack.org/static/challenges/13406_d7fa07291de630ace1055895f9ae208b.py
class AES:
    block_size = 16
    rcon = (0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36)

    sbox = OptimizedSBox.sbox
    inv_sbox = OptimizedSBox.inv_sbox

    def __init__(self, key):
        self.round_keys = self.expand_key([i for i in key])

    @staticmethod
    def transpose(m):
        return [m[4 * j + i] for i in range(4) for j in range(4)]
    
    @staticmethod
    def xor(a: list, b: list) -> list:
        return [x + y for x, y in zip(a, b)]
    
    @classmethod
    def expand_key(cls, key) -> list[list]:
        round_keys = [key]

        for i in range(10):
            round_key = []
            first = round_keys[i][:4]
            last = round_keys[i][-4:]
            last = last[1:] + [last[0]]
            last = [cls.sbox(i) for i in last]

            round_key.extend(cls.xor(cls.xor(first, last), [cls.rcon[i + 1], 0, 0, 0]))
            for j in range(0, 12, 4):
                round_key.extend(cls.xor(round_key[j:j + 4], round_keys[i][j + 4:j + 8]))
            round_keys.append(round_key)

        for i in range(len(round_keys)):
            round_keys[i] = cls.transpose(round_keys[i])

        return round_keys

    def add_round_key(self, state: list, i: int) -> list:
        return self.xor(state, self.round_keys[i])

    @classmethod
    def mix_columns(cls, state: list) -> list:
        s = [None] * cls.block_size
        for i in range(4):
            s[i] = 2 * state[i] + 3 * state[i + 4] + state[i + 8] + state[i + 12]
            s[i + 4] = state[i] + 2 * state[i + 4] + 3 * state[i + 8] + state[i + 12]
            s[i + 8] = state[i] + state[i + 4] + 2 * state[i + 8] + 3 * state[i + 12]
            s[i + 12] = 3 * state[i] + state[i + 4] + state[i + 8] + 2 * state[i + 12]
        return s

    @classmethod
    def inv_mix_columns(cls, state: list) -> list:
        s = [None] * cls.block_size
        for i in range(4):
            s[i] = 14 * state[i] + 11 * state[i + 4] + 13 * state[i + 8] + 9 * state[i + 12]
            s[i + 4] = 9 * state[i] + 14 * state[i + 4] + 11 * state[i + 8] + 13 * state[i + 12]
            s[i + 8] = 13 * state[i] + 9 * state[i + 4] + 14 * state[i + 8] + 11 * state[i + 12]
            s[i + 12] = 11 * state[i] + 13 * state[i + 4] + 9 * state[i + 8] + 14 * state[i + 12]
        return s

    @staticmethod
    def shift_rows(state: list) -> list:
        return [
            state[0], state[1], state[2], state[3],
            state[5], state[6], state[7], state[4],
            state[10], state[11], state[8], state[9],
            state[15], state[12], state[13], state[14]
        ]

    @staticmethod
    def inv_shift_rows(state: list) -> list:
        return [
            state[0], state[1], state[2], state[3],
            state[7], state[4], state[5], state[6],
            state[10], state[11], state[8], state[9],
            state[13], state[14], state[15], state[12]
        ]

    @classmethod
    def sub_bytes(cls, state: list) -> list:
        return [cls.sbox(i) for i in state]

    @classmethod
    def inv_sub_bytes(cls, state: list) -> list:
        return [cls.inv_sbox(i) for i in state]
    
    def encrypt_block(self, state: list) -> list:
        state = self.add_round_key(state, 0)

        for i in range(1, 10):
            state = self.sub_bytes(state)
            state = self.shift_rows(state)
            state = self.mix_columns(state)
            state = self.add_round_key(state, i)

        state = self.sub_bytes(state)
        state = self.shift_rows(state)
        state = self.add_round_key(state, 10)
        return state

    def decrypt_block(self, state: list) -> list:
        state = self.add_round_key(state, 10)
        state = self.inv_shift_rows(state)
        state = self.inv_sub_bytes(state)

        for i in reversed(range(1, 10)):
            state = self.add_round_key(state, i)
            state = self.inv_mix_columns(state)
            state = self.inv_shift_rows(state)
            state = self.inv_sub_bytes(state)

        state = self.add_round_key(state, 0)
        return state

    def encrypt(self, pt: list) -> list:
        assert len(pt) % self.block_size == 0, "plaintext length must be multiple of block size"

        ct = []
        for i in range(0, len(pt), self.block_size):
            state = self.transpose(pt[i:i + self.block_size])
            state = self.encrypt_block(state)
            ct += self.transpose(state)
        return ct

    def decrypt(self, ct: list) -> list:
        assert len(ct) % self.block_size == 0, "ciphertext length must be multiple of block size"

        pt = []
        for i in range(0, len(ct), self.block_size):
            block = ct[i:i + self.block_size]
            state = self.transpose([c for c in block])
            state = self.decrypt_block(state)
            pt += self.transpose(state)
        return pt
    

if __name__ == "__main__":
    from Crypto.Cipher import AES as PyCryptoAES
    from .gf2e import GF2E as GF2EValue
    from ..wires import GF2E as GF2EWires
    from ..circuit import BinaryGate, BinaryCircuit
    import os

    # Test correctness
    modulus = 0x11b  # AES modulus x^8 + x^4 + x^3 + x + 1
    key = [GF2EValue(i, modulus) for i in os.urandom(16)]
    key_bytes = bytes(i.value for i in key)
    pt = [GF2EValue(i, modulus) for i in os.urandom(16)]
    pt_bytes = bytes(i.value for i in pt)
    aes = AES(key)
    aes_pyc = PyCryptoAES.new(key_bytes, PyCryptoAES.MODE_ECB)
    ct = aes.encrypt(pt)
    ct_bytes = aes_pyc.encrypt(pt_bytes)
    assert bytes(i.value for i in ct) == ct_bytes
    assert aes.decrypt(ct) == pt

    bytes_to_bits = lambda b: [(b[i // 8] >> (i % 8)) & 1 for i in range(len(b) * 8)]
    bits_to_bytes = lambda bits: bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(len(bits) // 8))

    # AES-ENC circuit construction
    binary_circuit = BinaryCircuit()
    key = []
    for _ in range(16):
        byte = GF2EWires(binary_circuit, binary_circuit.add_garbler_inputs(8), modulus)
        key.append(byte)
    pt = []
    for _ in range(16):
        byte = GF2EWires(binary_circuit, binary_circuit.add_evaluator_inputs(8), modulus)
        pt.append(byte)
    ct = []
    for _ in range(16):
        byte = GF2EWires(binary_circuit, binary_circuit.add_outputs(8), modulus)
        ct.append(byte)
    aes = AES(key)
    for x, y in zip(aes.encrypt(pt), ct):
        x == y

    # AES-ENC circuit evaluation
    key_bytes = os.urandom(16)
    pt_bytes = os.urandom(16)
    ct_bytes = PyCryptoAES.new(key_bytes, PyCryptoAES.MODE_ECB).encrypt(pt_bytes)
    assert ct_bytes == bits_to_bytes(binary_circuit.eval_plain(
        garbler_values=bytes_to_bits(key_bytes),
        evaluator_values=bytes_to_bits(pt_bytes)
    ))
    print("AES-ENC circuit stats:")
    print(f"  Number of gates: {len(binary_circuit.gates)}")
    print(f"  Number of AND gates: {sum(isinstance(gate, BinaryGate.And) for gate in binary_circuit.gates)}")
    print(f"  Number of NOT gates: {sum(isinstance(gate, BinaryGate.Not) for gate in binary_circuit.gates)}")

    # AES-DEC circuit construction
    binary_circuit = BinaryCircuit()
    key = []
    for _ in range(16):
        byte = GF2EWires(binary_circuit, binary_circuit.add_garbler_inputs(8), modulus)
        key.append(byte)
    ct = []
    for _ in range(16):
        byte = GF2EWires(binary_circuit, binary_circuit.add_evaluator_inputs(8), modulus)
        ct.append(byte)
    pt = []
    for _ in range(16):
        byte = GF2EWires(binary_circuit, binary_circuit.add_outputs(8), modulus)
        pt.append(byte)
    aes = AES(key)
    for x, y in zip(aes.decrypt(ct), pt):
        x == y
    
    # AES-DEC circuit evaluation
    key_bytes = os.urandom(16)
    pt_bytes = os.urandom(16)
    ct_bytes = PyCryptoAES.new(key_bytes, PyCryptoAES.MODE_ECB).encrypt(pt_bytes)
    assert pt_bytes == bits_to_bytes(binary_circuit.eval_plain(
        garbler_values=bytes_to_bits(key_bytes),
        evaluator_values=bytes_to_bits(ct_bytes)
    ))
    print("AES-DEC circuit stats:")
    print(f"  Number of gates: {len(binary_circuit.gates)}")
    print(f"  Number of AND gates: {sum(isinstance(gate, BinaryGate.And) for gate in binary_circuit.gates)}")
    print(f"  Number of NOT gates: {sum(isinstance(gate, BinaryGate.Not) for gate in binary_circuit.gates)}")
