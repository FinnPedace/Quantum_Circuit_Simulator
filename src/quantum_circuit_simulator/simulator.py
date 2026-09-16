import numpy as np
from qiskit import QuantumCircuit
from .config import SimulationConfig
from .result import SimulationResult
import numpy as np
from qiskit import QuantumCircuit
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

        # Basis-Achsen für den Statevector-Tensor: [0, 1, ..., N-1]
        state_axes = list(range(num_qubits))  # Indizes der Qubits im Statevector-Tensor

        # Schritt 4: Gate-Schleife
        for instruction in circuit.data:
            op = instruction.operation
            op_name = op.name

            # Barrieren und Messungen verändern den Statevector nicht
            if op_name in ["barrier", "measure"]:
                continue

            if op_name == "cx":
                control_qubit = circuit.find_bit(instruction.qubits[0]).index
                target_qubit = circuit.find_bit(instruction.qubits[1]).index

                control_output_idx = num_qubits
                target_output_idx = num_qubits + 1

                gate_axes = [
                    control_output_idx,
                    target_output_idx,
                    control_qubit,
                    target_qubit,
                ]
                out_axes = list(state_axes)
                out_axes[control_qubit] = control_output_idx
                out_axes[target_qubit] = target_output_idx

                tensor = np.einsum(
                    CNOT_TENSOR,
                    gate_axes,
                    tensor,
                    state_axes,
                    out_axes,
                )
            else:
                # Es ist ein gültiges Ein-Qubit-Gate
                matrix = op.to_matrix()
                # Exakte Bestimmung des Qubit-Indexes
                target_qubit = circuit.find_bit(instruction.qubits[0]).index

                # Für die Kontraktion wird ein Index benötigt, der nicht
                # in state_axes vorkommt. Wir nutzen dafür einfach num_qubits.
                out_idx = num_qubits

                # Die 2x2-Matrix hat die Achsen [Output, Input]
                gate_axes = [out_idx, target_qubit]

                # Der resultierende Tensor hat dieselben Achsen wie vorher,
                # nur am target_qubit steht der neue out_idx
                out_axes = list(state_axes)
                out_axes[target_qubit] = out_idx

                # Tensor-Kontraktion ausführen
                tensor = np.einsum(matrix, gate_axes, tensor, state_axes, out_axes)

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
