from ..circuit import WireId, BinaryCircuit

__all__ = ['GF2E']


class GF2E:
    def __init__(self, binary_circuit: BinaryCircuit, wires: list[WireId], modulus: int):
        """ Initialize a GF(2^e) element with the given binary circuit, wires, and modulus. """
        if not isinstance(binary_circuit, BinaryCircuit):
            raise TypeError("binary_circuit must be of type BinaryCircuit")
        if not isinstance(wires, list) or not all(isinstance(w, WireId) for w in wires):
            raise TypeError("wires must be a list of integers")
        if not isinstance(modulus, int):
            raise TypeError("modulus must be an integer")
        self.binary_circuit = binary_circuit
        self.degree = modulus.bit_length() - 1
        if len(wires) != self.degree:
            raise ValueError(f"number of wires {len(wires)} does not match field degree {self.degree}")
        self.modulus = modulus
        self.wires = wires  # little-endian representation, wires[0] is least significant bit

    def __add_constant(self, constant: int) -> 'GF2E':
        """ Add an integer constant to the element. """
        if not isinstance(constant, int):
            raise TypeError("constant must be an integer")
        if not 0 <= constant < (1 << self.degree):
            raise ValueError(f"integer {constant} exceeds field size for modulus {self.modulus}")
        
        binary_circuit = self.binary_circuit
        result_wires = self.wires.copy()
        for i in range(self.degree):
            if (constant >> i) & 1:
                result_wires[i] = binary_circuit.add_not_gate(result_wires[i])
        return GF2E(self.binary_circuit, result_wires, self.modulus)

    def __add__(self, other: 'GF2E') -> 'GF2E':
        """ Add the element to another element or an integer constant. """
        if isinstance(other, int):
            return self.__add_constant(other)
        if not isinstance(other, GF2E):
            raise TypeError("other must be of type GF2E")
        if self.modulus != other.modulus:
            raise ValueError("cannot add elements from different fields")
        if self.binary_circuit != other.binary_circuit:
            raise ValueError("cannot add elements from different circuits")
        
        binary_circuit = self.binary_circuit
        result_wires = []
        for w1, w2 in zip(self.wires, other.wires):
            result_wire = binary_circuit.add_xor_gate(w1, w2)
            result_wires.append(result_wire)
        return GF2E(self.binary_circuit, result_wires, self.modulus)
        
    __sub__ = __add__  # addition and subtraction are the same in GF(2^e)

    def __mul_constant(self, constant: int) -> 'GF2E':
        """ Multiply the element by an integer constant. """
        if not isinstance(constant, int):
            raise TypeError("constant must be an integer")
        if not 0 <= constant < (1 << self.degree):
            raise ValueError(f"integer {constant} exceeds field size for modulus {self.modulus}")
        
        if constant == 0:
            raise ValueError("multiplication by zero is not supported since it's constant")
        if constant == 1:
            return GF2E(self.binary_circuit, self.wires.copy(), self.modulus)
        
        binary_circuit = self.binary_circuit
        shifted_wires = self.wires.copy()
        result_wires = shifted_wires.copy() if constant & 1 else None
        for i in range(1, self.degree):
            if not (constant >> i):
                break  # no more contributions
            # shift left by one (multiply by x)
            last = shifted_wires.pop()
            shifted_wires.insert(0, last)
            for j in range(1, self.degree):
                if (self.modulus >> j) & 1:
                    shifted_wires[j] = binary_circuit.add_xor_gate(last, shifted_wires[j])
            if (constant >> i) & 1:
                if result_wires is None:
                    result_wires = shifted_wires.copy()
                else:
                    result_wires = [binary_circuit.add_xor_gate(rw, sw) for rw, sw in zip(result_wires, shifted_wires)]
        assert result_wires is not None, "this should not happen"
        return GF2E(self.binary_circuit, result_wires, self.modulus)

    def __mul__(self, other: 'GF2E') -> 'GF2E':
        """ Multiply the element by another element or an integer constant. """
        if isinstance(other, int):
            return self.__mul_constant(other)
        if not isinstance(other, GF2E):
            raise TypeError("other must be of type GF2E")
        if self.modulus != other.modulus:
            raise ValueError("cannot multiply elements from different fields")
        if self.binary_circuit != other.binary_circuit:
            raise ValueError("cannot multiply elements from different circuits")
        
        binary_circuit = self.binary_circuit
        shifted_wires = self.wires.copy()
        result_wires = [binary_circuit.add_and_gate(w1, other.wires[0]) for w1 in self.wires]
        for i in range(1, self.degree):
            # shift left by one (multiply by x)
            last = shifted_wires.pop()
            shifted_wires.insert(0, last)
            for j in range(1, self.degree):
                if (self.modulus >> j) & 1:
                    shifted_wires[j] = binary_circuit.add_xor_gate(last, shifted_wires[j])
            # add contribution of other.wires[i]
            for j in range(self.degree):
                product_wire = binary_circuit.add_and_gate(shifted_wires[j], other.wires[i])
                result_wires[j] = binary_circuit.add_xor_gate(result_wires[j], product_wire)
        return GF2E(self.binary_circuit, result_wires, self.modulus)
    
    def __rmul__(self, other: int) -> 'GF2E':
        """ Multiply the element by an element from the left. Assumes other is an integer. """
        if not isinstance(other, int):
            raise TypeError(f"other must be an integer but got {type(other)}")
        return self.__mul_constant(other)
    
    def __pow__(self, exponent: int) -> 'GF2E':
        """ Raise the element to the given exponent. """
        if not isinstance(exponent, int):
            raise TypeError("exponent must be an integer")
        
        exp = exponent % ((1 << self.degree) - 1)
        if exp == 0:
            raise ValueError("exponentiation to zero is not supported since it's constant")
        if exp == 1:
            return GF2E(self.binary_circuit, self.wires.copy(), self.modulus)
        
        base = GF2E(self.binary_circuit, self.wires.copy(), self.modulus)
        result = base if exp & 1 else None
        exp >>= 1
        while exp > 0:
            base = base * base
            if exp & 1:
                if result is None:
                    result = base
                else:
                    result = result * base
            exp >>= 1
        assert result is not None, "this should not happen"
        return result

    def __lshift__(self, rotation: int) -> 'GF2E':
        """ Left rotate the wires by the given amount. """
        if not isinstance(rotation, int):
            raise TypeError("rotation must be an integer")
        rotation = rotation % self.degree
        rotated_wires = self.wires[-rotation:] + self.wires[:-rotation]
        return GF2E(self.binary_circuit, rotated_wires, self.modulus)

    def __rshift__(self, rotation: int) -> 'GF2E':
        """ Right rotate the wires by the given amount. """
        if not isinstance(rotation, int):
            raise TypeError("rotation must be an integer")
        rotation = rotation % self.degree
        rotated_wires = self.wires[rotation:] + self.wires[:rotation]
        return GF2E(self.binary_circuit, rotated_wires, self.modulus)

    def __repr__(self) -> str:
        wire_str = ', '.join(str(w) for w in self.wires)
        return f"GF2E([{wire_str}], modulus={self.modulus:0{self.degree + 1}b})"

    def __eq__(self, other: 'GF2E') -> None:
        """ Add equality constraints between this element and another GF2E element. """
        if not isinstance(other, GF2E):
            raise TypeError("equality constraint other must be of type GF2E")
        if self.modulus != other.modulus:
            raise ValueError("cannot compare elements from different fields")
        binary_circuit = self.binary_circuit
        for i in range(self.degree):
            binary_circuit.add_equality_constraint(self.wires[i], other.wires[i])

    def __ne__(self, other: 'GF2E') -> None:
        raise NotImplementedError("inequality constraints are not supported for GF2E elements")


if __name__ == "__main__":
    # Check correctness by building simple circuits
    from ..circuits.gf2e import GF2E as GF2EValue
    GF2EWires = GF2E
    from ..circuit import BinaryCircuit
    import secrets

    i2b = lambda x, n: [(x >> i) & 1 for i in range(n)]
    modulus = 0x11b  # x^8 + x^4 + x^3 + x + 1
    binary_circuit = BinaryCircuit()
    a_wires = GF2EWires(binary_circuit, binary_circuit.add_garbler_inputs(8), modulus)
    b_wires = GF2EWires(binary_circuit, binary_circuit.add_garbler_inputs(8), modulus)
    c_wires = GF2EWires(binary_circuit, binary_circuit.add_outputs(8), modulus)
    
    # Test addition between wires:
    a_value = secrets.randbits(8)
    b_value = secrets.randbits(8)
    c_value = (GF2EValue(a_value, modulus) + GF2EValue(b_value, modulus)).value
    a_wires + b_wires == c_wires
    assert i2b(c_value, 8) == binary_circuit.eval_plain(
        garbler_values=i2b(a_value, 8) + i2b(b_value, 8),
        evaluator_values=[]
    )
    binary_circuit.clear_gates()

    # Test addition with constant:
    a_value = secrets.randbits(8)
    constant = secrets.randbits(8)
    c_value = (GF2EValue(a_value, modulus) + GF2EValue(constant, modulus)).value
    a_wires + constant == c_wires
    assert i2b(c_value, 8) == binary_circuit.eval_plain(
        garbler_values=i2b(a_value, 8) + [0] * 8,  # b_wires could be anything
        evaluator_values=[]
    )
    binary_circuit.clear_gates()

    # Test multiplication between wires:
    a_value = secrets.randbits(8)
    b_value = secrets.randbits(8)
    c_value = (GF2EValue(a_value, modulus) * GF2EValue(b_value, modulus)).value
    a_wires * b_wires == c_wires
    assert i2b(c_value, 8) == binary_circuit.eval_plain(
        garbler_values=i2b(a_value, 8) + i2b(b_value, 8),
        evaluator_values=[]
    )
    binary_circuit.clear_gates()

    # Test multiplication with constant:
    a_value = secrets.randbits(8)
    constant = secrets.randbits(8)
    c_value = (GF2EValue(a_value, modulus) * GF2EValue(constant, modulus)).value
    a_wires * constant == c_wires
    assert i2b(c_value, 8) == binary_circuit.eval_plain(
        garbler_values=i2b(a_value, 8) + [0] * 8,  # b_wires could be anything
        evaluator_values=[]
    )
    binary_circuit.clear_gates()
