"""Contract tests comparing the public simulator API with Qiskit Aer."""

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator

from quantum_circuit_simulator.api import simulate
from quantum_circuit_simulator.config import SimulationConfig


def aer_reference_statevector(circuit: QuantumCircuit) -> np.ndarray:
    """Return Aer's exact final statevector before final measurements."""
    reference_circuit = circuit.remove_final_measurements(inplace=False)
    reference_circuit.save_statevector()
    result = AerSimulator(method="statevector").run(reference_circuit).result()
    return np.asarray(result.get_statevector().data)


def assert_statevectors_equivalent(
    actual: np.ndarray,
    expected: np.ndarray,
) -> None:
    """Compare statevectors while allowing a physically irrelevant global phase."""
    np.testing.assert_equal(actual.shape, expected.shape)
    pivot = np.flatnonzero(np.abs(expected) > 1e-12)[0]
    phase = actual[pivot] / expected[pivot]
    np.testing.assert_allclose(np.abs(phase), 1.0)
    np.testing.assert_allclose(actual, phase * expected)


@pytest.mark.parametrize("gate_name", ["x", "y", "z", "h"])
def test_single_qubit_gate_matches_aer(gate_name: str) -> None:
    """Test that the simulator's single-qubit gates match Aer's results."""
    circuit = QuantumCircuit(1)
    getattr(circuit, gate_name)(0)

    result = simulate(circuit)

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )
    assert result.counts is None


def test_parametric_single_qubit_gate_matches_aer() -> None:
    """Test that the simulator's parametric single-qubit gates match Aer's results."""

    circuit = QuantumCircuit(1)
    circuit.rx(np.pi / 3, 0)

    result = simulate(circuit)

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )


def test_custom_unitary_gate_matches_aer() -> None:
    """Test that the simulator's custom unitary gate matches Aer's results."""
    circuit = QuantumCircuit(1)
    unitary = np.array([[0, 1j], [1j, 0]], dtype=complex)
    circuit.append(UnitaryGate(unitary), [0])

    result = simulate(circuit)

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )


def test_deterministic_measurement_has_expected_counts() -> None:
    """Test that the simulator's measurement results match Aer's results for a deterministic circuit."""
    circuit = QuantumCircuit(1)
    circuit.x(0)
    circuit.measure_all()

    result = simulate(circuit, SimulationConfig(shots=100, seed=42))

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )
    assert result.counts == {"1": 100}


def test_bell_state_matches_aer_and_has_valid_counts() -> None:
    """Test that the simulator's Bell state circuit matches Aer's results and has valid measurement counts."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure_all()

    result = simulate(circuit, SimulationConfig(shots=1_000, seed=42))

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )
    assert set(result.counts) <= {"00", "11"}
    assert sum(result.counts.values()) == 1_000


def test_cnot_with_non_adjacent_qubits_matches_aer() -> None:
    """Test that the simulator's CNOT gate with non-adjacent qubits matches Aer's results."""
    circuit = QuantumCircuit(3)
    circuit.x(0)
    circuit.cx(0, 2)
    circuit.measure_all()

    result = simulate(circuit, SimulationConfig(shots=100, seed=42))

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )
    assert result.counts == {"101": 100}


def random_supported_circuit(seed: int) -> QuantumCircuit:
    """Create a reproducible circuit from only the project's supported gates."""
    random_generator = np.random.default_rng(seed)
    circuit = QuantumCircuit(3)

    for step in range(12):
        if step % 3 == 2:
            control, target = random_generator.choice(3, size=2, replace=False)
            circuit.cx(int(control), int(target))
            continue

        qubit = int(random_generator.integers(3))
        gate_name = random_generator.choice(["x", "y", "z", "h", "rx"])
        if gate_name == "rx":
            circuit.rx(float(random_generator.uniform(-np.pi, np.pi)), qubit)
        else:
            getattr(circuit, gate_name)(qubit)

    circuit.measure_all()
    return circuit


def test_random_supported_circuit_matches_aer() -> None:
    """Test that a random circuit made from only the project's supported gates matches Aer's results."""
    circuit = random_supported_circuit(seed=42)

    result = simulate(circuit, SimulationConfig(shots=100, seed=123))

    assert_statevectors_equivalent(
        result.statevector,
        aer_reference_statevector(circuit),
    )
    assert sum(result.counts.values()) == 100
