from .abstract import F, WireLabel
from .channel import Channel
from .crypto_random import CryptoRandom
import os

__all__ = ['Garbler']


class Garbler(F):
    def __init__(self, channel: Channel, seed: bytes = None):
        """ Initializes the Garbler with a communication channel and optional seed. """
        if not isinstance(channel, Channel):
            raise TypeError("channel must be an instance of Channel")
        self.channel = channel
        if seed is None:
            seed = os.urandom(32)
        self.seed = seed
        self.random = CryptoRandom(seed)
        super().__init__()
        self.delta = self.random.getrandbits(self.nbits) | 1  # ensure delta is odd
    
    def xor_gate(self, x: WireLabel, y: WireLabel) -> WireLabel:
        """ Implements the XOR gate using free-XOR technique https://encrypto.de/papers/KSS09.pdf. """
        return x ^ y

    def not_gate(self, x: WireLabel) -> WireLabel:
        """ Implements the NOT gate using free-XOR technique https://encrypto.de/papers/KSS09.pdf. """
        return x ^ self.delta
    
    def __garble_and_gate(self, A: WireLabel, B: WireLabel) -> WireLabel:
        """ Code adapted for Python from Rust fancy-garbling at https://github.com/GaloisInc/swanky/tree/dev. """
        # A, B are input wire labels
        # a, b are their respective values (0 or 1) which could be unknown to both parties
        D = self.delta
        gate_num = self.current_gate()

        r = B & 1  # secret value known only to the garbler (ev knows r+b, i.e. B if b = 0 or B+D if b = 1)
        g = gate_num.to_bytes(16, 'big')
        
        # X = H(A+αD) + αrD such that α == A & 1
        alpha = A & 1
        X1 = A ^ (D * alpha)

        # Y = H(B+βD) + (β + r)A such that β == B & 1
        beta = B & 1
        Y1 = B ^ (D * beta)

        AD = A ^ D
        BD = B ^ D

        a_selector = A & 1
        b_selector = B & 1

        B = BD if b_selector == 0 else B
        newA = AD if a_selector == 0 else A
        idx = r if a_selector == 0 else 0

        hashA, hashB, hashX, hashY = self.hash_wires([newA, B, X1, Y1], g)

        X = hashX ^ (D * (alpha * r % 2))
        Y = hashY

        gate0 = hashA ^ (X if idx == 0 else X ^ D)
        gate1 = hashB ^ (Y ^ A)

        return gate0, gate1, X ^ Y  # new wire label is Z = X + Y

    def and_gate(self, x: WireLabel, y: WireLabel) -> WireLabel:
        """ Garbles an AND gate using the half-gate technique https://eprint.iacr.org/2014/756.pdf. """
        gate0, gate1, z = self.__garble_and_gate(x, y)
        self.channel.send_wire(gate0)
        self.channel.send_wire(gate1)
        return z

    def encode_wire(self, bit: int) -> tuple[WireLabel, WireLabel]:
        """ Encodes an input bit into a wire label. """
        if bit not in (0, 1):
            raise ValueError("input bit must be 0 or 1")
        zero = self.random.getrandbits(self.nbits)
        enc = zero if bit == 0 else zero ^ self.delta
        return zero, enc
    
    def encode_wires(self, bits: list[int]) -> tuple[list[WireLabel], list[WireLabel]]:
        """ Encodes a list of input bits into wire labels. """
        return tuple(map(list, zip(*(self.encode_wire(bit) for bit in bits))))

    def evaluator_input(self) -> tuple[WireLabel, WireLabel]:
        """ Provides a the wire labels from which the evaluator can choose its input bit. """
        return self.encode_wire(1)
    
    def evaluator_inputs(self, n: int) -> list[tuple[WireLabel, WireLabel]]:
        """ Provides n wire labels from which the evaluator can choose its input bits. """
        return [self.evaluator_input() for _ in range(n)]

    def output_wire(self, zero: WireLabel) -> None:
        """ Sends the output wire hash to the evaluator. """
        output_num = self.current_output()
        tweak = output_num.to_bytes(16, 'big')
        one = zero ^ self.delta
        zero, one = self.hash_wires([zero, one], tweak)
        self.channel.send_wire(zero)
        self.channel.send_wire(one)

    def output_wires(self, zeros: list[WireLabel]) -> None:
        """ Sends the output wire hashes to the evaluator. """
        for zero in zeros:
            self.output_wire(zero)
