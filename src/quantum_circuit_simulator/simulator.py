from typing import Literal

import numpy as np
from qiskit import QuantumCircuit

from .alt_numpy_einsum import apply_cnot_gate, apply_single_qubit_gate
from .config import SimulationConfig
from .result import SimulationResult

CNOT_TENSOR = np.zeros((2, 2, 2, 2), dtype=complex)
for control_input in range(2):
    for target_input in range(2):
        CNOT_TENSOR[
            control_input,
            target_input ^ control_input,
            control_input,
            target_input,
        ] = 1


class StatevectorSimulator:
    """Statevector-Simulator mit Backend-Auswahl und optionaler Gate Fusion.

    :param backend: ``"einsum"`` für NumPy oder ``"numba"`` für die
        kompilierten Blockschleifen.
    :param gate_fusion: Fusioniert aufeinanderfolgende Ein-Qubit-Gates, wenn
        dieser Wert wahr ist.
    """

    def __init__(
        self,
        *,
        backend: Literal["einsum", "numba"] = "einsum",
        gate_fusion: bool = True,
    ) -> None:
        if backend not in ("einsum", "numba"):
            raise ValueError("backend must be 'einsum' or 'numba'")
        self.backend = backend
        self.gate_fusion = gate_fusion

    def _apply_single_qubit_gate(
        self,
        tensor: np.ndarray,
        matrix: np.ndarray,
        target_qubit: int,
        num_qubits: int,
    ) -> np.ndarray:
        """Apply one (possibly fused) matrix to a state tensor."""
        if self.backend == "numba":
            return apply_single_qubit_gate(
                tensor,
                matrix,
                target_qubit,
                num_qubits,
            )

        state_axes = list(range(num_qubits))
        output_index = num_qubits
        output_axes = list(state_axes)
        output_axes[target_qubit] = output_index

        return np.einsum(
            matrix,
            [output_index, target_qubit],
            tensor,
            state_axes,
            output_axes,
        )

    def _apply_cnot_gate(
        self,
        tensor: np.ndarray,
        control_qubit: int,
        target_qubit: int,
        num_qubits: int,
    ) -> np.ndarray:
        """Apply CNOT using the selected numerical backend."""
        if self.backend == "numba":
            return apply_cnot_gate(
                tensor,
                control_qubit,
                target_qubit,
                num_qubits,
            )

        control_output_idx = num_qubits
        target_output_idx = num_qubits + 1
        state_axes = list(range(num_qubits))
        gate_axes = [
            control_output_idx,
            target_output_idx,
            control_qubit,
            target_qubit,
        ]
        output_axes = list(state_axes)
        output_axes[control_qubit] = control_output_idx
        output_axes[target_qubit] = target_output_idx

        return np.einsum(
            CNOT_TENSOR,
            gate_axes,
            tensor,
            state_axes,
            output_axes,
        )

    def _flush_fused_gates(
        self,
        tensor: np.ndarray,
        fused_gates: dict[int, np.ndarray],
        num_qubits: int,
    ) -> np.ndarray:
        """Apply all pending single-qubit matrices and clear the buffer."""
        for target_qubit, matrix in fused_gates.items():
            tensor = self._apply_single_qubit_gate(
                tensor,
                matrix,
                target_qubit,
                num_qubits,
            )
        fused_gates.clear()
        return tensor

    def _validate_circuit(self, circuit: QuantumCircuit) -> None:
        """Prüft, ob der Circuit nur unitäre Gates und CNOT-Gates enthält."""
        if len(circuit.cregs) > 1:
            raise NotImplementedError(
                "Mehrere Classical Registers werden nicht unterstützt."
            )

        measurement_seen = (
            False  # Stellt sicher, dass keine Gates nach Messungen auftreten
        )
        measured_qubits = (
            set()
        )  # Hält die Menge der gemessenen Qubits, um Teilmessungen zu erkennen

        for instruction in circuit.data:
            op = instruction.operation
            op_name = op.name

            if op_name == "barrier":
                continue

            if op_name == "measure":
                measurement_seen = True
                measured_qubits.update(instruction.qubits)
                continue

            if measurement_seen:  # Gates nach Messungen sind verboten
                raise NotImplementedError("Gates nach Messungen sind verboten.")

            if op_name == "cx":  # CNOT-Gate ist erlaubt
                continue

            if hasattr(op, "to_matrix"):
                try:
                    matrix = op.to_matrix()
                    if matrix.shape == (2, 2):  # Ein-Qubit-Gate
                        continue
                except Exception:
                    pass

            raise NotImplementedError(
                f"Die Operation '{op_name}' ist nicht implementiert undwird nicht unterstützt."
            )

        if (
            measurement_seen and len(measured_qubits) != circuit.num_qubits
        ):  # Alle Qubits müssen gemessen werden, Teilmessungen sind nicht erlaubt
            raise NotImplementedError("Teilmessungen sind nicht erlaubt.")

    def simulate(
        self, circuit: QuantumCircuit, config: SimulationConfig
    ) -> SimulationResult:
        """Simuliert den gegebenen QuantumCircuit und gibt das Ergebnis als SimulationResult zurück.
        Dazu wird der Statevector des Circuits mithilfe von Tensor-Kontraktion berechnet.
        Falls Messungen im Circuit vorhanden sind, werden auch die Counts generiert."""
        num_qubits = circuit.num_qubits  # Anzahl der Qubits im Circuit

        # Schritt 2: Validierung
        self._validate_circuit(circuit)  # Ruft die Vaildierungsfunktion auf.

        # Schritt 3: Initialisierung
        # Startzustand |0...0> als 1D-Array
        state = np.zeros(2**num_qubits, dtype=complex)
        state[0] = 1.0 + 0.0j

        # Umformen in N-dimensionalen Tensor mit Qiskit-Basisordnung (Fortran-Layout)
        tensor = np.reshape(state, (2,) * num_qubits, order="F")

        # Aufeinanderfolgende Ein-Qubit-Gates werden pro Qubit gesammelt.
        # Ein späteres Gate U2 muss links multipliziert werden: U2 @ U1.
        fused_gates: dict[int, np.ndarray] = {}

        # Schritt 4: Gate-Schleife mit Gate Fusion
        for instruction in circuit.data:
            op = instruction.operation
            op_name = op.name

            # Strukturelle Instruktionen bilden eine Fusionsgrenze, verändern
            # den Statevector selbst aber nicht.
            if op_name in ["barrier", "measure"]:
                tensor = self._flush_fused_gates(tensor, fused_gates, num_qubits)
                continue

            if op_name == "cx":
                tensor = self._flush_fused_gates(tensor, fused_gates, num_qubits)
                control_qubit = circuit.find_bit(instruction.qubits[0]).index
                target_qubit = circuit.find_bit(instruction.qubits[1]).index
                tensor = self._apply_cnot_gate(
                    tensor,
                    control_qubit,
                    target_qubit,
                    num_qubits,
                )
            else:
                target_qubit = circuit.find_bit(instruction.qubits[0]).index
                matrix = np.asarray(op.to_matrix(), dtype=complex)
                if self.gate_fusion:
                    previous_matrix = fused_gates.get(target_qubit)
                    fused_gates[target_qubit] = (
                        matrix if previous_matrix is None else matrix @ previous_matrix
                    )
                else:
                    tensor = self._apply_single_qubit_gate(
                        tensor,
                        matrix,
                        target_qubit,
                        num_qubits,
                    )

        tensor = self._flush_fused_gates(tensor, fused_gates, num_qubits)

        # Schritt 5: Tensor zurück in 1D-Statevector wandeln
        final_sv = np.reshape(tensor, -1, order="F")

        # Schritt 6: Counts durch Sampling generieren (falls Messungen existieren)
        counts = None
        if circuit.num_clbits > 0:
            # 1. Wahrscheinlichkeiten der einzelnen Zustände berechnen
            probabilities = np.abs(final_sv) ** 2

            # 2. Zufallsgenerator mit dem Seed aus der Config initialisieren (für Reproduzierbarkeit)
            rng = np.random.default_rng(config.seed)

            # 3. Indizes basierend auf den Wahrscheinlichkeiten ziehen
            # len(probabilities) entspricht 2^num_qubits
            sampled_indices = rng.choice(
                len(probabilities), size=config.shots, p=probabilities
            )

            # 4. Gezogene Indizes in Qiskit-kompatible Bitstrings umwandeln und zählen
            counts = {}
            for idx in sampled_indices:
                # Formatiert den Integer als Binär-String mit passender Länge und führenden Nullen.
                # Ein Index wie 1 wird bei 2 Qubits zu "01", was exakt Qiskits Basisordnung entspricht.
                bitstring = format(idx, f"0{num_qubits}b")
                counts[bitstring] = counts.get(bitstring, 0) + 1

        return SimulationResult(statevector=final_sv, counts=counts)
