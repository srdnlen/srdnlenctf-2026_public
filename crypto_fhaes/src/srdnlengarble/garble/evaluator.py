from .abstract import F, WireLabel
from .channel import Channel

__all__ = ['Evaluator']


class Evaluator(F):
    def __init__(self, channel: Channel):
        """ Initializes the Evaluator with a communication channel. """
        if not isinstance(channel, Channel):
            raise TypeError("channel must be an instance of Channel")
        self.channel = channel
        super().__init__()
    
    def xor_gate(self, x: WireLabel, y: WireLabel) -> WireLabel:
        """ Implements the XOR gate using free-XOR technique https://encrypto.de/papers/KSS09.pdf. """
        return x ^ y

    def not_gate(self, x: WireLabel) -> WireLabel:
        """ Implements the NOT gate using free-XOR technique https://encrypto.de/papers/KSS09.pdf. """
        return x  # no-op for evaluator
    
    def __evaluate_and_gate(self, A: WireLabel, B: WireLabel, gate0: WireLabel, gate1: WireLabel) -> WireLabel:
        """ Code adapted for Python from Rust fancy-garbling at https://github.com/GaloisInc/swanky/tree/dev. """
        gate_num = self.current_gate()
        g = gate_num.to_bytes(16, 'big')
        
        hashA, hashB = self.hash_wires([A, B], g)

        L = hashA if (A & 1) == 0 else hashA ^ gate0
        R = hashB if (B & 1) == 0 else hashB ^ gate1

        return L ^ R ^ (A * (B & 1))

    def and_gate(self, x: WireLabel, y: WireLabel) -> WireLabel:
        """ Evaluates an AND gate using the half-gate technique https://eprint.iacr.org/2014/756.pdf. """
        gate0 = self.channel.read_wire()
        gate1 = self.channel.read_wire()
        z = self.__evaluate_and_gate(x, y, gate0, gate1)
        return z

    def output_wire(self, wire: WireLabel) -> bool:
        """ Reads the output wire hashes from the channel and determines the output bit. """
        output_num = self.current_output()
        tweak = output_num.to_bytes(16, 'big')
        (wire,) = self.hash_wires([wire], tweak)
        zero = self.channel.read_wire()
        one = self.channel.read_wire()
        if wire == zero:
            return False
        elif wire == one:
            return True
        else:
            raise ValueError("Output wire does not match any expected label")

    def output_wires(self, wires: list[WireLabel]) -> list[bool]:
        """ Reads multiple output wire hashes from the channel and determines the output bits. """
        return [self.output_wire(wire) for wire in wires]
