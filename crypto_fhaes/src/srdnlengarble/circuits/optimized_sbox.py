from ..circuit import BinaryCircuit

__all__ = ["OptimizedSBox"]


# Based on https://eprint.iacr.org/2011/332.pdf Figures 5 to 9
class OptimizedSBox:
    # Figure 5
    top_forward = """
T1 = U0 + U3
T2 = U0 + U5
T3 = U0 + U6
T4 = U3 + U5
T5 = U4 + U6
T6 = T1 + T5
T7 = U1 + U2
T8 = U7 + T6
T9 = U7 + T7
T10 = T6 + T7
T11 = U1 + U5
T12 = U2 + U5
T13 = T3 + T4
T14 = T6 + T11
T15 = T5 + T11
T16 = T5 + T12
T17 = T9 + T16
T18 = U3 + U7
T19 = T7 + T18
T20 = T1 + T19
T21 = U6 + U7
T22 = T7 + T21
T23 = T2 + T22
T24 = T2 + T10
T25 = T20 + T17
T26 = T3 + T16
T27 = T1 + T12
"""
    # Figure 6
    top_reverse = """
T23 = U0 + U3
T22 = U1 # U3
T2 = U0 # U1
T1 = U3 + U4
T24 = U4 # U7
R5 = U6 + U7
T8 = U1 # T23
T19 = T22 + R5
T9 = U7 # T1
T10 = T2 + T24
T13 = T2 + R5
T3 = T1 + R5
T25 = U2 # T1
R13 = U1 + U6
T17 = U2 # T19
T20 = T24 + R13
T4 = U4 + T8
R17 = U2 # U5
R18 = U5 # U6
R19 = U2 # U4
Y5 = U0 + R17
T6 = T22 + R17
T16 = R13 + R19
T27 = T1 + R18
T15 = T10 + T27
T14 = T10 + R18
T26 = T3 + T16
"""
    # Figure 7: D = U7 if forward else D = Y5
    shared = """
M1 = T13 x T6
M2 = T23 x T8
M3 = T14 + M1
M4 = T19 x D
M5 = M4 + M1
M6 = T3 x T16
M7 = T22 x T9
M8 = T26 + M6
M9 = T20 x T17
M10 = M9 + M6
M11 = T1 x T15
M12 = T4 x T27
M13 = M12 + M11
M14 = T2 x T10
M15 = M14 + M11
M16 = M3 + M2
M17 = M5 + T24
M18 = M8 + M7
M19 = M10 + M15
M20 = M16 + M13
M21 = M17 + M15
M22 = M18 + M13
M23 = M19 + T25
M24 = M22 + M23
M25 = M22 x M20
M26 = M21 + M25
M27 = M20 + M21
M28 = M23 + M25
M29 = M28 x M27
M30 = M26 x M24
M31 = M20 x M23
M32 = M27 x M31
M33 = M27 + M25
M34 = M21 x M22
M35 = M24 x M34
M36 = M24 + M25
M37 = M21 + M29
M38 = M32 + M33
M39 = M23 + M30
M40 = M35 + M36
M41 = M38 + M40
M42 = M37 + M39
M43 = M37 + M38
M44 = M39 + M40
M45 = M42 + M41
M46 = M44 x T6
M47 = M40 x T8
M48 = M39 x D
M49 = M43 x T16
M50 = M38 x T9
M51 = M37 x T17
M52 = M42 x T15
M53 = M45 x T27
M54 = M41 x T10
M55 = M44 x T13
M56 = M40 x T23
M57 = M39 x T19
M58 = M43 x T3
M59 = M38 x T22
M60 = M37 x T20
M61 = M42 x T1
M62 = M45 x T4
M63 = M41 x T2
"""
    # Figure 8: outputs are S0...S7
    bottom_forward = """
L0 = M61 + M62
L1 = M50 + M56
L2 = M46 + M48
L3 = M47 + M55
L4 = M54 + M58
L5 = M49 + M61
L6 = M62 + L5
L7 = M46 + L3
L8 = M51 + M59
L9 = M52 + M53
L10 = M53 + L4
L11 = M60 + L2
L12 = M48 + M51
L13 = M50 + L0
L14 = M52 + M61
L15 = M55 + L1
L16 = M56 + L0
L17 = M57 + L1
L18 = M58 + L8
L19 = M63 + L4
L20 = L0 + L1
L21 = L1 + L7
L22 = L3 + L12
L23 = L18 + L2
L24 = L15 + L9
L25 = L6 + L10
L26 = L7 + L9
L27 = L8 + L10
L28 = L11 + L14
L29 = L11 + L17
S0 = L6 + L24
S1 = L16 # L26
S2 = L19 # L28
S3 = L6 + L21
S4 = L20 + L22
S5 = L25 + L29
S6 = L13 # L27
S7 = L6 # L23
"""
    # Figure 9: outputs are W0...W7
    bottom_reverse = """
P0 = M52 + M61
P1 = M58 + M59
P2 = M54 + M62
P3 = M47 + M50
P4 = M48 + M56
P5 = M46 + M51
P6 = M49 + M60
P7 = P0 + P1
P8 = M50 + M53
P9 = M55 + M63
P10 = M57 + P4
P11 = P0 + P3
P12 = M46 + M48
P13 = M49 + M51
P14 = M49 + M62
P15 = M54 + M59
P16 = M57 + M61
P17 = M58 + P2
P18 = M63 + P5
P19 = P2 + P3
P20 = P4 + P6
P22 = P2 + P7
P23 = P7 + P8
P24 = P5 + P7
P25 = P6 + P10
P26 = P9 + P11
P27 = P10 + P18
P28 = P11 + P25
P29 = P15 + P20
W0 = P13 + P22
W1 = P26 + P29
W2 = P17 + P28
W3 = P12 + P22
W4 = P23 + P27
W5 = P19 + P24
W6 = P14 + P23
W7 = P9 + P16
"""
    
    @staticmethod
    def parse_line(line: str, vars: dict, binary_circuit: BinaryCircuit):
        """ Parse a line of the form 'LHS = RHS' and update vars and binary_circuit accordingly. """
        lhs, rhs = line.strip().split(" = ")
        lhs, rhs = lhs.strip(), rhs.strip()
        if " + " in rhs:  # XOR
            x, y = rhs.split(" + ")
            vars[lhs] = binary_circuit.add_xor_gate(vars[x], vars[y])
        elif " # " in rhs:  # XNOR
            x, y = rhs.split(" # ")
            temp = binary_circuit.add_xor_gate(vars[x], vars[y])
            vars[lhs] = binary_circuit.add_not_gate(temp)
        elif " x " in rhs:  # AND
            x, y = rhs.split(" x ")
            vars[lhs] = binary_circuit.add_and_gate(vars[x], vars[y])
        else:
            raise ValueError(f"invalid line: {line}")

    @classmethod
    def __sbox_optimized(cls, byte):
        """ Apply the optimized S-box transformation to a GF2E element using binary circuits. """
        from ..wires import GF2E
        assert isinstance(byte, GF2E)
        if byte.modulus != 0x11b:
            raise ValueError("only AES modulus is supported")
        binary_circuit = byte.binary_circuit
        # Input wires are in reverse order: from most significant to least significant
        vars = {f"U{i}": byte.wires[7 - i] for i in range(8)}
        # Forward transformation
        for line in cls.top_forward.strip().split("\n"):
            cls.parse_line(line, vars, binary_circuit)
        # Shared transformation
        vars["D"] = vars["U7"]
        for line in cls.shared.strip().split("\n"):
            cls.parse_line(line, vars, binary_circuit)
        # Bottom transformation
        for line in cls.bottom_forward.strip().split("\n"):
            cls.parse_line(line, vars, binary_circuit)
        # Output wires are in reverse order: from most significant to least significant
        output_wires = [vars[f"S{i}"] for i in reversed(range(8))]
        return GF2E(binary_circuit, output_wires, byte.modulus)

    @classmethod
    def sbox(cls, byte):
        """ Apply the S-box transformation to a GF2E element. """
        from ..wires import GF2E
        if isinstance(byte, GF2E):
            return cls.__sbox_optimized(byte)
        from .gf2e import GF2E
        if not isinstance(byte, GF2E):
            raise TypeError("byte must be a GF2E element")
        if byte.modulus != 0x11b:
            raise ValueError("only AES modulus is supported")
        # Non-linear transformation
        byte = byte**-1
        # Affine transformation
        byte = byte + (byte >> 4) + (byte >> 5) + (byte >> 6) + (byte >> 7) + 0b01100011
        return byte
    
    @classmethod
    def __inv_sbox_optimized(cls, byte):
        """ Apply the optimized inverse S-box transformation to a GF2E element using binary circuits. """
        from ..wires import GF2E
        assert isinstance(byte, GF2E)
        if byte.modulus != 0x11b:
            raise ValueError("only AES modulus is supported")
        binary_circuit = byte.binary_circuit
        # Input wires are in reverse order: from most significant to least significant
        vars = {f"U{i}": byte.wires[7 - i] for i in range(8)}
        # Reverse top transformation
        for line in cls.top_reverse.strip().split("\n"):
            cls.parse_line(line, vars, binary_circuit)
        # Shared transformation
        vars["D"] = vars["Y5"]
        for line in cls.shared.strip().split("\n"):
            cls.parse_line(line, vars, binary_circuit)
        # Reverse bottom transformation
        for line in cls.bottom_reverse.strip().split("\n"):
            cls.parse_line(line, vars, binary_circuit)
        # Output wires are in reverse order: from most significant to least significant
        output_wires = [vars[f"W{i}"] for i in reversed(range(8))]
        return GF2E(binary_circuit, output_wires, byte.modulus)
    
    @classmethod
    def inv_sbox(cls, byte):
        """ Apply the inverse S-box transformation to a GF2E element. """
        from ..wires import GF2E
        if isinstance(byte, GF2E):
            return cls.__inv_sbox_optimized(byte)
        from .gf2e import GF2E
        if not isinstance(byte, GF2E):
            raise TypeError("byte must be a GF2E element")
        if byte.modulus != 0x11b:
            raise ValueError("only AES modulus is supported")
        # Inverse affine transformation
        byte = byte + 0b01100011
        byte = (byte >> 2) + (byte >> 5) + (byte >> 7)
        # Inverse non-linear transformation
        byte = byte**-1
        return byte


if __name__ == "__main__":
    from .gf2e import GF2E as GF2EValue
    from ..wires import GF2E as GF2EWires

    SBOX = (
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76, 
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0, 
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15, 
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75, 
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84, 
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf, 
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8, 
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2, 
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73, 
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb, 
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79, 
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08, 
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a, 
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e, 
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf, 
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
    )
    modulus = 0x11b  # AES modulus x^8 + x^4 + x^3 + x + 1

    # Test correctness for GF2EValue
    for x in range(256):
        x = GF2EValue(x, modulus)
        assert OptimizedSBox.inv_sbox(OptimizedSBox.sbox(x)) == x
        assert OptimizedSBox.sbox(x).value == SBOX[x.value]

    # Test correctness for GF2EWires

    i2b = lambda x: [(x >> i) & 1 for i in range(8)]
    
    binary_circuit = BinaryCircuit()
    x_wires = GF2EWires(binary_circuit, binary_circuit.add_garbler_inputs(8), modulus)
    y_wires = GF2EWires(binary_circuit, binary_circuit.add_outputs(8), modulus)
    y_wires == OptimizedSBox.sbox(x_wires)
    for x_value in range(256):
        y_value = SBOX[x_value]
        assert i2b(y_value) == binary_circuit.eval_plain(
            garbler_values=i2b(x_value),
            evaluator_values=[],
        )
    
    binary_circuit = BinaryCircuit()
    x_wires = GF2EWires(binary_circuit, binary_circuit.add_garbler_inputs(8), modulus)
    x_wires == OptimizedSBox.inv_sbox(OptimizedSBox.sbox(x_wires))
    for x_value in range(256):
        # should crash internally if x != inv_sbox(sbox(x))
        binary_circuit.eval_plain(
            garbler_values=i2b(x_value),
            evaluator_values=[],
        )
