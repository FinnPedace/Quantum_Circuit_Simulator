"""Tests for the explicit single-qubit statevector implementation."""

import numpy as np
import pytest

from quantum_circuit_simulator.alt_numpy_einsum import (
    apply_single_qubit_gate,
    apply_single_qubit_unitary,
)


def einsum_reference(
    statevector: np.ndarray,
    matrix: np.ndarray,
    target_qubit: int,
    num_qubits: int,
) -> np.ndarray:
    """Apply a matrix using the simulator's existing einsum convention."""
    tensor = np.reshape(statevector, (2,) * num_qubits, order="F")
    state_axes = list(range(num_qubits))
    output_index = num_qubits
    output_axes = list(state_axes)
    output_axes[target_qubit] = output_index
    result = np.einsum(
        matrix,
        [output_index, target_qubit],
        tensor,
        state_axes,
        output_axes,
    )
    return np.reshape(result, -1, order="F")


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 5])
def test_all_target_qubits_match_einsum(num_qubits: int) -> None:
    """The explicit pair loops match einsum for every possible target."""
    rng = np.random.default_rng(100 + num_qubits)
    statevector = rng.normal(size=2**num_qubits) + 1j * rng.normal(
        size=2**num_qubits
    )
    matrix = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))

    for target_qubit in range(num_qubits):
        actual = apply_single_qubit_unitary(
            statevector,
            matrix,
            target_qubit,
            num_qubits,
        )
        expected = einsum_reference(
            statevector,
            matrix,
            target_qubit,
            num_qubits,
        )
        np.testing.assert_allclose(actual, expected, atol=1e-12)


def test_target_qubit_one_uses_expected_index_pairs() -> None:
    """For q1, the pairs are (0,2), (1,3), (4,6), and (5,7)."""
    statevector = np.arange(8, dtype=complex)
    swap = np.array([[0, 1], [1, 0]], dtype=complex)

    result = apply_single_qubit_unitary(statevector, swap, 1, 3)

    np.testing.assert_array_equal(result, [2, 3, 0, 1, 6, 7, 4, 5])


def test_input_statevector_is_not_modified() -> None:
    """Reading one pair never overwrites data needed by a later result."""
    statevector = np.array([1, 2, 3, 4], dtype=complex)
    original = statevector.copy()
    matrix = np.array([[1, 2], [3, 4]], dtype=complex)

    apply_single_qubit_unitary(statevector, matrix, 0, 2)

    np.testing.assert_array_equal(statevector, original)


def test_tensor_wrapper_preserves_simulator_shape_and_order() -> None:
    """The wrapper accepts and returns the simulator's Fortran-order tensor."""
    statevector = np.arange(8, dtype=complex)
    tensor = np.reshape(statevector, (2, 2, 2), order="F")
    matrix = np.array([[1, 2j], [-3j, 4]], dtype=complex)

    result = apply_single_qubit_gate(tensor, matrix, 2, 3)
    expected = einsum_reference(statevector, matrix, 2, 3)

    assert result.shape == tensor.shape
    np.testing.assert_allclose(
        np.reshape(result, -1, order="F"),
        expected,
        atol=1e-12,
    )
