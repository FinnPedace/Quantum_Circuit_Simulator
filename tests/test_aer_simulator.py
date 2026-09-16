import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.circuit.random import random_circuit
from quantum_circuit_simulator.aer_simulator import AerSimulatorWrapper
from quantum_circuit_simulator.config import SimulationConfig


def test_no_measurement_returns_statevector_and_no_counts() -> None:
    """Test Hadamard gate on a single qubit without measurement returns the correct statevector and no counts."""
    circuit = QuantumCircuit(1)
    circuit.h(0)

    result = AerSimulatorWrapper().simulate(
        circuit,
        SimulationConfig(),
    )

    expected = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])

    np.testing.assert_allclose(result.statevector, expected)
    assert result.counts is None


def test_x_gate_with_measurement_has_deterministic_counts() -> None:
    """Test X gate on a single qubit with measurement returns the correct statevector and deterministic counts."""
    circuit = QuantumCircuit(1)
    circuit.x(0)
    circuit.measure_all()

    result = AerSimulatorWrapper().simulate(
        circuit,
        SimulationConfig(shots=100),
    )

    np.testing.assert_allclose(
        result.statevector,
        np.array([0, 1]),
    )
    assert result.counts == {"1": 100}


def aer_reference_statevector(circuit: QuantumCircuit) -> np.ndarray:
    """Compute the reference statevector for a given circuit."""
    reference_circuit = circuit.remove_final_measurements(inplace=False)
    reference_circuit.save_statevector()

    result = (
        AerSimulator(method="statevector")
        .run(
            reference_circuit,
        )
        .result()
    )

    return np.asarray(result.get_statevector().data)


def test_random_circuit_matches_aer_reference() -> None:
    circuit = random_circuit(
        num_qubits=3,
        depth=5,
        max_operands=1,
        measure=True,
        seed=42,
    )

    result = AerSimulatorWrapper().simulate(
        circuit,
        SimulationConfig(shots=100, seed=123),
    )

    expected = aer_reference_statevector(circuit)

    np.testing.assert_allclose(
        result.statevector,
        expected,
    )
    assert sum(result.counts.values()) == 100
