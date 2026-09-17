"""Cross-check all numerical backends and gate-fusion modes."""

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quantum_circuit_simulator.config import SimulationConfig
from quantum_circuit_simulator.simulator import StatevectorSimulator


def aer_reference_statevector(circuit: QuantumCircuit) -> np.ndarray:
    """Return Aer's exact statevector for a circuit without measurements."""
    reference_circuit = circuit.copy()
    reference_circuit.save_statevector()
    result = AerSimulator(method="statevector").run(reference_circuit).result()
    return np.asarray(result.get_statevector().data)


@pytest.mark.parametrize("backend", ["einsum", "numba"])
@pytest.mark.parametrize("gate_fusion", [False, True])
def test_backend_and_fusion_combinations_match_aer(
    backend: str,
    gate_fusion: bool,
) -> None:
    """All four custom-simulator variants produce the Aer statevector."""
    circuit = QuantumCircuit(4)
    for layer in range(5):
        for qubit in range(4):
            angle = (layer + 1) * (qubit + 1) / 13
            circuit.rx(angle, qubit)
            circuit.ry(-angle / 2, qubit)
            circuit.rz(angle / 3, qubit)
        circuit.cx(layer % 4, (layer + 1) % 4)

    result = StatevectorSimulator(
        backend=backend,
        gate_fusion=gate_fusion,
    ).simulate(circuit, SimulationConfig())

    np.testing.assert_allclose(
        result.statevector,
        aer_reference_statevector(circuit),
        atol=1e-12,
    )


@pytest.mark.parametrize(
    ("gate_fusion", "expected_applications"),
    [(False, 3), (True, 1)],
)
def test_gate_fusion_flag_controls_number_of_applications(
    monkeypatch,
    gate_fusion: bool,
    expected_applications: int,
) -> None:
    """Disabling fusion applies each single-qubit matrix immediately."""
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.rx(0.4, 0)
    circuit.rz(-0.7, 0)

    simulator = StatevectorSimulator(gate_fusion=gate_fusion)
    original_apply = simulator._apply_single_qubit_gate
    applied_matrices: list[np.ndarray] = []

    def record_apply(tensor, matrix, target_qubit, num_qubits):
        applied_matrices.append(matrix.copy())
        return original_apply(tensor, matrix, target_qubit, num_qubits)

    monkeypatch.setattr(simulator, "_apply_single_qubit_gate", record_apply)
    simulator.simulate(circuit, SimulationConfig())

    assert len(applied_matrices) == expected_applications


def test_unknown_backend_is_rejected() -> None:
    """Backend names fail early instead of silently selecting an implementation."""
    with pytest.raises(ValueError, match="backend"):
        StatevectorSimulator(backend="unknown")
