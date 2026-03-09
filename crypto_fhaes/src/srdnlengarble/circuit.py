from .garble import F, WireLabel
import dataclasses, re

__all__ = ['BinaryGate', 'BinaryCircuit', 'WireId']


WireId = int


class BinaryGate:
    @dataclasses.dataclass(frozen=True)
    class Not:
        input_wire: WireId
        output_wire: WireId
    
    @dataclasses.dataclass(frozen=True)
    class Xor:
        input_left: WireId
        input_right: WireId
        output_wire: WireId

    @dataclasses.dataclass(frozen=True)
    class And:
        input_left: WireId
        input_right: WireId
        output_wire: WireId
    
    @dataclasses.dataclass(frozen=True)
    class EqualityConstraint:
        lhs: WireId
        rhs: WireId


class BinaryCircuit:
    def __init__(self):
        """ Initialize an empty binary circuit. """
        self.wire_index = 0
        self.garbler_inputs = []
        self.evaluator_inputs = []
        self.outputs = []
        self.gates = []

    @property
    def num_garbler_inputs(self) -> int:
        """ Number of garbler input wires in the circuit. """
        return len(self.garbler_inputs)

    @property
    def num_evaluator_inputs(self) -> int:
        """ Number of evaluator input wires in the circuit. """
        return len(self.evaluator_inputs)
    
    @property
    def num_outputs(self) -> int:
        """ Number of output wires in the circuit. """
        return len(self.outputs)

    def add_garbler_input(self) -> WireId:
        """ Add a garbler input wire to the circuit and return its wire ID. """
        wire_id = self.wire_index
        self.wire_index += 1
        self.garbler_inputs.append(wire_id)
        return wire_id
    
    def add_garbler_inputs(self, n: int) -> list[WireId]:
        """ Add n garbler input wires to the circuit and return their wire IDs. """
        return [self.add_garbler_input() for _ in range(n)]
    
    def add_evaluator_input(self) -> WireId:
        """ Add an evaluator input wire to the circuit and return its wire ID. """
        wire_id = self.wire_index
        self.wire_index += 1
        self.evaluator_inputs.append(wire_id)
        return wire_id
    
    def add_evaluator_inputs(self, n: int) -> list[WireId]:
        """ Add n evaluator input wires to the circuit and return their wire IDs. """
        return [self.add_evaluator_input() for _ in range(n)]
    
    def add_output(self) -> WireId:
        """ Add an output wire to the circuit and return its wire ID. """
        wire_id = self.wire_index
        self.wire_index += 1
        self.outputs.append(wire_id)
        return wire_id
    
    def add_outputs(self, n: int) -> list[WireId]:
        """ Add n output wires to the circuit and return their wire IDs. """
        return [self.add_output() for _ in range(n)]

    def add_not_gate(self, input_wire: WireId) -> WireId:
        """ Add a NOT gate to the circuit and return its output wire ID. """
        output_wire = self.wire_index
        self.wire_index += 1
        gate = BinaryGate.Not(input_wire=input_wire, output_wire=output_wire)
        self.gates.append(gate)
        return output_wire
    
    def add_xor_gate(self, input_left: WireId, input_right: WireId) -> WireId:
        """ Add an XOR gate to the circuit and return its output wire ID. """
        output_wire = self.wire_index
        self.wire_index += 1
        gate = BinaryGate.Xor(input_left=input_left, input_right=input_right, output_wire=output_wire)
        self.gates.append(gate)
        return output_wire
    
    def add_and_gate(self, input_left: WireId, input_right: WireId) -> WireId:
        """ Add an AND gate to the circuit and return its output wire ID. """
        output_wire = self.wire_index
        self.wire_index += 1
        gate = BinaryGate.And(input_left=input_left, input_right=input_right, output_wire=output_wire)
        self.gates.append(gate)
        return output_wire
    
    def add_equality_constraint(self, lhs: WireId, rhs: WireId) -> None:
        """ Add an equality constraint between two wires to the circuit. """
        gate = BinaryGate.EqualityConstraint(lhs=lhs, rhs=rhs)
        self.gates.append(gate)

    def __eq__(self, other: object) -> bool:
        """ Check if two circuits are the same using identity comparison only. """
        if not isinstance(other, BinaryCircuit):
            return False
        return self is other  # identity comparison since equivalence checking is too expensive

    def __ne__(self, other: object) -> bool:
        """ Check if two circuits are different using identity comparison only. """
        return not self.__eq__(other)
    
    def copy(self) -> 'BinaryCircuit':
        """ Create a deep copy of the circuit. """
        new_circuit = BinaryCircuit()
        new_circuit.wire_index = self.wire_index
        # wires are just integers, so shallow copy is sufficient
        new_circuit.garbler_inputs = self.garbler_inputs.copy()
        new_circuit.evaluator_inputs = self.evaluator_inputs.copy()
        new_circuit.outputs = self.outputs.copy()
        # gates are immutable dataclasses, so shallow copy is sufficient
        new_circuit.gates = self.gates.copy()
        return new_circuit

    def clear(self) -> None:
        """ Clear the circuit to an empty state. """
        self.wire_index = 0
        self.garbler_inputs.clear()
        self.evaluator_inputs.clear()
        self.outputs.clear()
        self.gates.clear()

    def clear_gates(self) -> None:
        """ Clear all gates from the circuit, preserving inputs and outputs. """
        self.wire_index = len(self.garbler_inputs) + len(self.evaluator_inputs) + len(self.outputs)
        self.gates.clear()

    def save(self, filename: str) -> None:
        """ Save the circuit to a file following Bristol format. """

        if not isinstance(filename, str):
            raise ValueError("filename must be a string")
        if not filename:
            raise ValueError("filename cannot be empty")
        if not self.gates:
            raise ValueError("cannot save an empty circuit")
        if not self.garbler_inputs and not self.evaluator_inputs:
            raise ValueError("circuit must have at least one input to be saved")
        if not self.outputs:
            raise ValueError("circuit must have at least one output to be saved")
        current_id = 0
        for wire_id in self.garbler_inputs + self.evaluator_inputs + self.outputs:
            if wire_id != current_id:
                raise ValueError("IO wire IDs must be contiguous starting from 0 to save circuit: "
                                 "first garbler inputs, then evaluator inputs, then outputs")
            current_id += 1

        # normalize circuit since we have custom gate EqualityConstraint
        map_eq_wires = dict()
        for gate in self.gates:
            if isinstance(gate, BinaryGate.EqualityConstraint):
                x, y = gate.lhs, gate.rhs
                if x == y:  # no-op
                    continue
                if x > y:  # give preference to smaller wire ID
                    x, y = y, x
                map_eq_wires[y] = x

        def find_representative(wire: WireId) -> WireId:
            nonlocal map_eq_wires
            while wire in map_eq_wires:
                wire = map_eq_wires[wire]
            return wire

        gates = []
        for gate in self.gates:
            if isinstance(gate, BinaryGate.EqualityConstraint):
                continue
            elif isinstance(gate, BinaryGate.Not):
                input_wire = find_representative(gate.input_wire)
                output_wire = find_representative(gate.output_wire)
                gates.append(BinaryGate.Not(input_wire=input_wire, output_wire=output_wire))
            elif isinstance(gate, BinaryGate.Xor):
                input_left = find_representative(gate.input_left)
                input_right = find_representative(gate.input_right)
                output_wire = find_representative(gate.output_wire)
                gates.append(BinaryGate.Xor(input_left=input_left, input_right=input_right, output_wire=output_wire))
            elif isinstance(gate, BinaryGate.And):
                input_left = find_representative(gate.input_left)
                input_right = find_representative(gate.input_right)
                output_wire = find_representative(gate.output_wire)
                gates.append(BinaryGate.And(input_left=input_left, input_right=input_right, output_wire=output_wire))
            else:
                raise ValueError(f"unsupported gate type for saving: {type(gate)}")
        
        # wire IDs may be non-contiguous after normalization; so the Bristol format is not strictly followed
        with open(filename, 'w') as f:
            f.write(f"{len(gates)} {self.wire_index}\n")
            f.write(f"{len(self.garbler_inputs)} {len(self.evaluator_inputs)} {len(self.outputs)}\n\n")
            for gate in gates:
                if isinstance(gate, BinaryGate.Not):
                    f.write(f"1 1 {gate.input_wire} {gate.output_wire} INV\n")
                elif isinstance(gate, BinaryGate.Xor):
                    f.write(f"2 1 {gate.input_left} {gate.input_right} {gate.output_wire} XOR\n")
                elif isinstance(gate, BinaryGate.And):
                    f.write(f"2 1 {gate.input_left} {gate.input_right} {gate.output_wire} AND\n")
                else:
                    assert False, "should not reach here"
    
    @classmethod
    def load(cls, filename: str) -> 'BinaryCircuit':
        """ Load a circuit from a file following Bristol format. """
        circuit = cls()

        with open(filename, 'r') as f:
            header = f.readline().strip()
            match_ = re.match(r"(\d+)\s+(\d+)", header)
            if match_ is None:
                raise ValueError("Invalid header format")
            num_gates, num_wires = map(int, match_.groups())
            input_output_line = f.readline().strip()
            match_ = re.match(r"(\d+)\s+(\d+)\s+(\d+)", input_output_line)
            if match_ is None:
                raise ValueError("Invalid input/output line format")
            num_garbler_inputs, num_evaluator_inputs, num_outputs = map(int, match_.groups())
            
            circuit.add_garbler_inputs(num_garbler_inputs)
            circuit.add_evaluator_inputs(num_evaluator_inputs)
            circuit.add_outputs(num_outputs)

            for line in f:
                line = line.strip()
                if not line:
                    continue

                match1 = re.match(r"1 1 (\d+) (\d+) INV", line)
                match2 = re.match(r"2 1 (\d+) (\d+) (\d+) (XOR|AND)", line)
                if match1 is None and match2 is None:
                    raise ValueError(f'Invalid gate line format: "{line}"')
                
                if match1 is not None:
                    input_wire = int(match1.group(1))
                    if input_wire < 0 or input_wire >= num_wires:
                        raise ValueError("invalid input wire ID in NOT gate")
                    output_wire = int(match1.group(2))
                    if output_wire < 0 or output_wire >= num_wires:
                        raise ValueError("invalid output wire ID in NOT gate")
                    circuit.gates.append(
                        BinaryGate.Not(input_wire=input_wire, output_wire=output_wire)
                    )

                if match2 is not None:
                    input_left = int(match2.group(1))
                    if input_left < 0 or input_left >= num_wires:
                        raise ValueError("invalid left input wire ID in binary gate")
                    input_right = int(match2.group(2))
                    if input_right < 0 or input_right >= num_wires:
                        raise ValueError("invalid right input wire ID in binary gate")
                    output_wire = int(match2.group(3))
                    if output_wire < 0 or output_wire >= num_wires:
                        raise ValueError("invalid output wire ID in binary gate")
                    gate_type = match2.group(4)
                    if gate_type == "XOR":
                        circuit.gates.append(
                            BinaryGate.Xor(input_left=input_left, input_right=input_right, output_wire=output_wire)
                        )
                    elif gate_type == "AND":
                        circuit.gates.append(
                            BinaryGate.And(input_left=input_left, input_right=input_right, output_wire=output_wire)
                        )
                    else:
                        assert False, "should not reach here"
            
            if len(circuit.gates) != num_gates:
                raise ValueError("number of gates in file does not match header")
        
        return circuit

    def eval_plain(self, garbler_values: list[int], evaluator_values: list[int]) -> list[int]:
        """ Evaluate the circuit in plain (non-garbled) form. """
        if len(garbler_values) != len(self.garbler_inputs):
            raise ValueError("invalid number of garbler input values")
        if len(evaluator_values) != len(self.evaluator_inputs):
            raise ValueError("invalid number of evaluator input values")
        if any(v not in (0, 1) for v in garbler_values):
            raise ValueError("garbler input values must be bits")
        if any(v not in (0, 1) for v in evaluator_values):
            raise ValueError("evaluator input values must be bits")
        
        wire_map = dict()
        for i, wire_id in enumerate(self.garbler_inputs):
            wire_map[wire_id] = garbler_values[i]
        for i, wire_id in enumerate(self.evaluator_inputs):
            wire_map[wire_id] = evaluator_values[i]
        
        for gate in self.gates:
            if isinstance(gate, BinaryGate.Xor):
                wire_map[gate.output_wire] = wire_map[gate.input_left] ^ wire_map[gate.input_right]
            elif isinstance(gate, BinaryGate.And):
                wire_map[gate.output_wire] = wire_map[gate.input_left] & wire_map[gate.input_right]
            elif isinstance(gate, BinaryGate.Not):
                wire_map[gate.output_wire] = wire_map[gate.input_wire] ^ 1
            elif isinstance(gate, BinaryGate.EqualityConstraint):
                if gate.lhs in wire_map and gate.rhs in wire_map:
                    if wire_map[gate.lhs] != wire_map[gate.rhs]:
                        raise ValueError("equality constraint violated during evaluation")
                elif gate.lhs in wire_map:
                    val = wire_map[gate.lhs]
                    wire_map[gate.rhs] = val
                elif gate.rhs in wire_map:
                    val = wire_map[gate.rhs]
                    wire_map[gate.lhs] = val
                else:
                    raise ValueError("cannot evaluate equality constraint with unknown wires")
            else:
                raise ValueError("unsupported gate type during evaluation")
        
        output_values = []
        for output_wire in self.outputs:
            if output_wire not in wire_map:
                raise ValueError("output wire has no computed value")
            output_values.append(wire_map[output_wire])
        return output_values

    def eval(
            self, 
            f: F, 
            garbler_inputs: list[WireLabel], 
            evaluator_inputs: list[WireLabel]
        ) -> None | list[WireLabel]:
        """ Evaluate the circuit using the provided garbler/evaluator implementation. """
        if not isinstance(f, F):
            raise ValueError("f must be an instance of F, i.e., Garbler or Evaluator")
        if not isinstance(garbler_inputs, list):
            raise ValueError("garbler inputs must be a list")
        if not isinstance(evaluator_inputs, list):
            raise ValueError("evaluator inputs must be a list")
        if len(garbler_inputs) != len(self.garbler_inputs):
            raise ValueError("invalid number of garbler inputs")
        if len(evaluator_inputs) != len(self.evaluator_inputs):
            raise ValueError("invalid number of evaluator inputs")
        if any(not isinstance(v, WireLabel) for v in garbler_inputs):
            raise ValueError("invalid garbler input type")
        if any(not isinstance(v, WireLabel) for v in evaluator_inputs):
            raise ValueError("invalid evaluator input type")
        
        wire_map = dict()
        for i, wire_id in enumerate(self.garbler_inputs):
            wire_map[wire_id] = garbler_inputs[i]
        for i, wire_id in enumerate(self.evaluator_inputs):
            wire_map[wire_id] = evaluator_inputs[i]
        
        for gate in self.gates:
            if isinstance(gate, BinaryGate.Xor):
                wire_map[gate.output_wire] = f.xor_gate(
                    wire_map[gate.input_left],
                    wire_map[gate.input_right]
                )
            elif isinstance(gate, BinaryGate.And):
                wire_map[gate.output_wire] = f.and_gate(
                    wire_map[gate.input_left],
                    wire_map[gate.input_right]
                )
            elif isinstance(gate, BinaryGate.Not):
                wire_map[gate.output_wire] = f.not_gate(
                    wire_map[gate.input_wire]
                )
            elif isinstance(gate, BinaryGate.EqualityConstraint):
                lhs = wire_map.get(gate.lhs, None)
                rhs = wire_map.get(gate.rhs, None)
                if lhs is not None and rhs is not None:
                    if lhs != rhs:
                        raise ValueError("equality constraint violated during evaluation")
                elif lhs is not None:
                    wire_map[gate.rhs] = lhs
                elif rhs is not None:
                    wire_map[gate.lhs] = rhs
                else:
                    raise ValueError("cannot evaluate equality constraint with unknown wires")
            else:
                raise ValueError("unsupported gate type during evaluation")
        
        output_values = []
        for output_wire in self.outputs:
            if output_wire not in wire_map:
                raise ValueError("output wire has no computed value")
            output_values.append(f.output_wire(wire_map[output_wire]))
        return None if all(v is None for v in output_values) else output_values
