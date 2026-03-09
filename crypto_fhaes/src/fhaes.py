from srdnlengarble import (
    BinaryCircuit, GF2E, AES
)

__all__ = ['FHAES']


class FHAES:
    def __init__(self):
        """ Initialize the FHAES instance with a binary circuit and AES key. """
        self.modulus = 0x11b  # AES modulus x^8 + x^4 + x^3 + x + 1
        self.binary_circuit = BinaryCircuit()
        self.key = []
        for _ in range(16):
            byte = GF2E(self.binary_circuit, self.binary_circuit.add_garbler_inputs(8), self.modulus)
            self.key.append(byte)
        self.__aes = None  # lazy initialization

    @property
    def aes(self) -> AES:
        """ Lazy initialization of the AES circuit to enable inputs and outputs definition before use. """
        if self.__aes is None:
            self.__aes = AES(self.key)
        return self.__aes

    def garbler_bytes(self, n: int) -> list[GF2E]:
        """ Create n garbler input bytes. """
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be a non-negative integer")
        bc = self.binary_circuit
        return [GF2E(bc, bc.add_garbler_inputs(8), self.modulus) for _ in range(n)]

    def evaluator_bytes(self, n: int) -> list[GF2E]:
        """ Create n evaluator input bytes. """
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be a non-negative integer")
        bc = self.binary_circuit
        return [GF2E(bc, bc.add_evaluator_inputs(8), self.modulus) for _ in range(n)]

    def output_bytes(self, n: int) -> list[GF2E]:
        """ Create n output bytes. """
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be a non-negative integer")
        bc = self.binary_circuit
        return [GF2E(bc, bc.add_outputs(8), self.modulus) for _ in range(n)]
    
    def encrypt(self, pt: list[GF2E]) -> list[GF2E]:
        """ Encrypt plaintext bytes using the AES circuit. """
        if not isinstance(pt, list) or any(not isinstance(b, GF2E) for b in pt) or len(pt) != 16:
            raise ValueError("pt must be a list of 16 GF2E bytes")
        return self.aes.encrypt(pt)
    
    def decrypt(self, ct: list[GF2E]) -> list[GF2E]:
        """ Decrypt ciphertext bytes using the AES circuit. """
        if not isinstance(ct, list) or any(not isinstance(b, GF2E) for b in ct) or len(ct) != 16:
            raise ValueError("ct must be a list of 16 GF2E bytes")
        return self.aes.decrypt(ct)
    
    def add(self, x: list[GF2E], y: list[GF2E]) -> list[GF2E]:
        """ Add two lists of GF2E bytes. """
        if not isinstance(x, list) or not isinstance(y, list) or len(x) != len(y):
            raise ValueError("x and y must be lists of the same length")
        if any(not isinstance(a, GF2E) for a in x) or any(not isinstance(b, GF2E) for b in y):
            raise ValueError("x and y must be lists of GF2E bytes")
        return [a + b for a, b in zip(x, y)]

    def multiply(self, x: list[GF2E], y: list[GF2E]) -> list[GF2E]:
        """ Multiply two lists of GF2E bytes. """
        if not isinstance(x, list) or not isinstance(y, list) or len(x) != len(y):
            raise ValueError("x and y must be lists of the same length")
        if any(not isinstance(a, GF2E) for a in x) or any(not isinstance(b, GF2E) for b in y):
            raise ValueError("x and y must be lists of GF2E bytes")
        return [a * b for a, b in zip(x, y)]
    
    def custom_circuit(self, x: list[GF2E], circuit: list[dict]) -> list[GF2E]:
        """ 
        Evaluate a custom binary circuit on the input GF2E bytes. 
        
        The circuit is defined as a list of gates, where each gate is a dict with keys:
        - 'type': str, one of 'EQ', 'NOT', 'AND', 'XOR'
        - 'inputs': list of custom labels (str)
        - 'output': custom label (str)

        The input wires are named x0, x1, ..., and output wires are named y0, y1, ...
        """
        if not isinstance(x, list) or any(not isinstance(b, GF2E) for b in x):
            raise ValueError("x must be a list of GF2E bytes")
        if not isinstance(circuit, list) or any(not isinstance(gate, dict) for gate in circuit):
            raise ValueError("circuit must be a list of gate dictionaries")
        bc = self.binary_circuit
        wires_map = dict()

        # input wires are named x0, x1, ...
        for i, byte in enumerate(x):
            for j in range(8):
                wires_map[f"x{i * 8 + j}"] = byte.wires[j]
        
        # evaluate the circuit
        add_gate = {
            'EQ': bc.add_equality_constraint, 
            'NOT': bc.add_not_gate, 
            'AND': bc.add_and_gate, 
            'XOR': bc.add_xor_gate
        }
        for gate in circuit:
            gate_type = gate.get('type')
            if gate_type not in add_gate:
                raise ValueError(f"unsupported gate type: {gate_type}")
            inputs = gate.get('inputs')
            if not all(isinstance(label, str) and label in wires_map for label in inputs):
                raise ValueError(f"input labels not found in wires_map: {inputs}")
            inputs = [wires_map[label] for label in inputs]
            output = gate.get('output')
            if not isinstance(output, str):
                raise ValueError(f"output wire must be a string: {output}")
            wires_map[output] = add_gate[gate_type](*inputs)

        # collect output wires named y0, y1, ...
        if not all(f"y{i * 8 + j}" in wires_map for i in range(len(x)) for j in range(8)):
            raise ValueError("output wires not found in wires_map")
        y = []
        for i in range(len(x)):
            wires = [wires_map[f"y{i * 8 + j}"] for j in range(8)]
            y.append(GF2E(bc, wires, self.modulus))
        return y
