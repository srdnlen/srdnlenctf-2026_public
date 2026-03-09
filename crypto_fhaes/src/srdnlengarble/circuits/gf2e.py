__all__ = ['GF2E']


class GF2E:
    def __init__(self, value: int, modulus: int):
        """ Initialize an element in GF(2^e) defined by the given modulus polynomial. """
        self.degree = modulus.bit_length() - 1
        self.modulus = modulus
        if value >= (1 << self.degree):
            raise ValueError(f"value {value} exceeds field size for modulus {modulus}")
        self.value = value
    
    def __add__(self, other: 'GF2E') -> 'GF2E':
        """ Addition in GF(2^e) is just XOR """
        if isinstance(other, int):
            other = GF2E(other, self.modulus)
        if not isinstance(other, GF2E):
            raise TypeError("other must be of type GF2E")
        if self.modulus != other.modulus:
            raise ValueError("cannot add elements from different fields")
        return GF2E(self.value ^ other.value, self.modulus)

    __sub__ = __add__  # Subtraction is the same as addition in GF(2^e)

    def __mul__(self, other: 'GF2E') -> 'GF2E':
        """ Multiplication in GF(2^m) """
        if isinstance(other, int):
            other = GF2E(other, self.modulus)
        if not isinstance(other, GF2E):
            raise TypeError("other must be of type GF2E")
        if self.modulus != other.modulus:
            raise ValueError("cannot multiply elements from different fields")
        
        result = 0
        a = self.value
        b = other.value
        mod = self.modulus
        deg = self.degree

        while b > 0:
            if b & 1:
                result ^= a
            a <<= 1
            if a & (1 << deg):
                a ^= mod
            b >>= 1
        return GF2E(result, mod)
    
    def __rmul__(self, other: int) -> 'GF2E':
        """ Right multiplication by an integer """
        if not isinstance(other, int):
            raise TypeError("other must be an integer")
        if not 0 <= other < (1 << self.degree):
            raise ValueError(f"integer {other} exceeds field size for modulus {self.modulus}")
        return self * GF2E(other, self.modulus)

    def __pow__(self, exponent: int) -> 'GF2E':
        """ Exponentiation in GF(2^e) using square-and-multiply """
        if not isinstance(exponent, int):
            raise TypeError("exponent must be an integer")
        
        result = GF2E(1, self.modulus)
        base = self
        exp = exponent % ((1 << self.degree) - 1)
        
        while exp > 0:
            if exp & 1:
                result *= base
            base *= base
            exp >>= 1
        return result
    
    def __lshift__(self, rotation: int) -> 'GF2E':
        """ Logical left rotation """
        if not isinstance(rotation, int):
            raise TypeError("rotation must be an integer")
        
        rotation = rotation % self.degree
        return GF2E(
            ((self.value << rotation) | (self.value >> (self.degree - rotation))) & ((1 << self.degree) - 1),
            self.modulus
        )
    
    def __rshift__(self, rotation: int) -> 'GF2E':
        """ Logical right rotation """
        if not isinstance(rotation, int):
            raise TypeError("rotation must be an integer")
        
        rotation = rotation % self.degree
        return GF2E(
            ((self.value >> rotation) | (self.value << (self.degree - rotation))) & ((1 << self.degree) - 1),
            self.modulus
        )
    
    def __repr__(self) -> str:
        return f"GF2E({self.value:0{self.degree}b}, modulus={self.modulus:0{self.degree + 1}b})"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, GF2E):
            return self.value == other.value and self.modulus == other.modulus
        if isinstance(other, int):
            return self.value == other
        return False
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
