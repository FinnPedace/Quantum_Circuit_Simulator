"""Tests for the statevector simulator's single-qubit gate fusion."""

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quantum_circuit_simulator.config import SimulationConfig
from quantum_circuit_simulator.simulator import StatevectorSimulator


def aer_reference_statevector(circuit: QuantumCircuit) -> np.ndarray:
    """Return Aer's exact final statevector."""
    reference_circuit = circuit.copy()
    reference_circuit.save_statevector()
    result = AerSimulator(method="statevector").run(reference_circuit).result()
    return np.asarray(result.get_statevector().data)


def assert_statevectors_equivalent(
    actual: np.ndarray,
    expected: np.ndarray,
) -> None:
    """Compare statevectors up to a global phase."""
    pivot = np.flatnonzero(np.abs(expected) > 1e-12)[0]
    phase = actual[pivot] / expected[pivot]
    np.testing.assert_allclose(np.abs(phase), 1.0, atol=1e-12)
    np.testing.assert_allclose(actual, phase * expected, atol=1e-12)


def test_consecutive_gates_are_fused_in_matrix_order(monkeypatch) -> None:
    """A run of gates on one qubit becomes one correctly ordered matrix."""
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.rx(0.37, 0)
    circuit.rz(-0.81, 0)

    expected_matrix = (
        circuit.data[2].operation.to_matrix()
        @ circuit.data[1].operation.to_matrix()
        @ circuit.data[0].operation.to_matrix()
    )
    applied_matrices: list[np.ndarray] = []
    simulator = StatevectorSimulator()
    original_apply = simulator._apply_single_qubit_gate

    def record_apply(tensor, matrix, target_qubit, num_qubits):
        applied_matrices.append(matrix.copy())
        return original_apply(tensor, matrix, target_qubit, num_qubits)

    monkeypatch.setattr(simulator, "_apply_single_qubit_gate", record_apply)
    result = simulator.simulate(circuit, SimulationConfig())

    assert len(applied_matrices) == 1
    np.testing.assert_allclose(applied_matrices[0], expected_matrix, atol=1e-12)
    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )


def test_gate_fusion_groups_independent_qubits(monkeypatch) -> None:
    """Independent single-qubit runs require one contraction per qubit."""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.x(1)
    circuit.ry(0.4, 0)
    circuit.s(1)
    circuit.z(0)
    circuit.rx(-0.2, 2)

    applied_qubits: list[int] = []
    simulator = StatevectorSimulator()
    original_apply = simulator._apply_single_qubit_gate

    def record_apply(tensor, matrix, target_qubit, num_qubits):
        applied_qubits.append(target_qubit)
        return original_apply(tensor, matrix, target_qubit, num_qubits)

    monkeypatch.setattr(simulator, "_apply_single_qubit_gate", record_apply)
    result = simulator.simulate(circuit, SimulationConfig())

    assert applied_qubits == [0, 1, 2]
    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )


def test_cnot_separates_fusion_groups_and_matches_aer(monkeypatch) -> None:
    """Gates on either side of an entangling gate are not fused together."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.rz(0.23, 0)
    circuit.x(1)
    circuit.cx(0, 1)
    circuit.ry(-0.61, 0)
    circuit.sx(0)
    circuit.z(1)

    applied_qubits: list[int] = []
    simulator = StatevectorSimulator()
    original_apply = simulator._apply_single_qubit_gate

    def record_apply(tensor, matrix, target_qubit, num_qubits):
        applied_qubits.append(target_qubit)
        return original_apply(tensor, matrix, target_qubit, num_qubits)

    monkeypatch.setattr(simulator, "_apply_single_qubit_gate", record_apply)
    result = simulator.simulate(circuit, SimulationConfig())

    assert applied_qubits == [0, 1, 0, 1]
    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )


def test_long_fused_circuit_matches_aer() -> None:
    """Backtest a longer circuit with several fusion and CNOT boundaries."""
    circuit = QuantumCircuit(4)
    for layer in range(10):
        angle = (layer + 1) / 10
        for qubit in range(4):
            circuit.rx(angle, qubit)
            circuit.ry(-angle / 2, qubit)
            circuit.rz(angle / 3, qubit)
        circuit.cx(layer % 4, (layer + 1) % 4)

    result = StatevectorSimulator().simulate(circuit, SimulationConfig())

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )
