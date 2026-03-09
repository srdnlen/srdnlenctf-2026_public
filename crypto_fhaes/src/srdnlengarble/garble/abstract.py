from abc import ABC, abstractmethod
import hashlib

__all__ = ['F', 'WireLabel']


WireLabel = int


class F(ABC):
    """ Base class for Garbler and Evaluator implementations. """

    def __init__(self):
        self.gate_count = 0
        self.output_count = 0
        self.nbits = 128  # number of bits in a wire label

    @abstractmethod
    def xor_gate(self, x: WireLabel, y: WireLabel) -> WireLabel:
        pass

    @abstractmethod
    def not_gate(self, x: WireLabel) -> WireLabel:
        pass

    @abstractmethod
    def and_gate(self, x: WireLabel, y: WireLabel) -> WireLabel:
        pass
    
    def current_gate(self) -> int:
        """ Returns the current gate number and increments the counter. """
        gate_num = self.gate_count
        self.gate_count += 1
        return gate_num
    
    def current_output(self) -> int:
        """ Returns the current output number and increments the counter. """
        output_num = self.output_count
        self.output_count += 1
        return output_num
    
    def hash_wires(self, wires: list[WireLabel], tweak: bytes) -> list[WireLabel]:
        """ Hash a list of labels with a given tweak. """
        if not isinstance(wires, list):
            raise TypeError("wires must be a list")
        if not all(isinstance(wire, WireLabel) for wire in wires):
            raise TypeError("all wires must be of type WireLabel (int)")
        if any(wire < 0 or wire.bit_length() > self.nbits for wire in wires):
            raise ValueError("all wires must be 128-bit non-negative integers")
        if not isinstance(tweak, bytes):
            raise TypeError("tweak must be bytes")
        
        hashed_labels = []
        for wire in wires:
            hasher = hashlib.shake_128()
            hasher.update(wire.to_bytes(self.nbits // 8, 'big'))
            hasher.update(tweak)
            hashed_label = hasher.digest(self.nbits // 8)
            hashed_labels.append(int.from_bytes(hashed_label, 'big'))
        return hashed_labels

    @abstractmethod
    def output_wire(self, wire: WireLabel) -> None | bool:
        pass

    @abstractmethod
    def output_wires(self, wires: list[WireLabel]) -> None | list[bool]:
        pass
