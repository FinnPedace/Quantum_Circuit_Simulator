"""Tests for the explicit statevector operations without einsum."""

import numpy as np
import pytest

from quantum_circuit_simulator.alt_numpy_einsum import (
    apply_cnot_gate,
    apply_cnot_statevector,
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


def cnot_einsum_reference(
    statevector: np.ndarray,
    control_qubit: int,
    target_qubit: int,
    num_qubits: int,
) -> np.ndarray:
    """Apply CNOT using the simulator's existing four-axis tensor."""
    cnot_tensor = np.zeros((2, 2, 2, 2), dtype=complex)
    for control_input in range(2):
        for target_input in range(2):
            cnot_tensor[
                control_input,
                target_input ^ control_input,
                control_input,
                target_input,
            ] = 1

    tensor = np.reshape(statevector, (2,) * num_qubits, order="F")
    state_axes = list(range(num_qubits))
    control_output = num_qubits
    target_output = num_qubits + 1
    output_axes = list(state_axes)
    output_axes[control_qubit] = control_output
    output_axes[target_qubit] = target_output

    result = np.einsum(
        cnot_tensor,
        [control_output, target_output, control_qubit, target_qubit],
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


@pytest.mark.parametrize("num_qubits", [2, 3, 5])
def test_cnot_matches_einsum_for_all_qubit_pairs(num_qubits: int) -> None:
    """Every ordered control/target combination matches the CNOT tensor."""
    rng = np.random.default_rng(200 + num_qubits)
    statevector = rng.normal(size=2**num_qubits) + 1j * rng.normal(
        size=2**num_qubits
    )

    for control_qubit in range(num_qubits):
        for target_qubit in range(num_qubits):
            if control_qubit == target_qubit:
                continue

            actual = apply_cnot_statevector(
                statevector,
                control_qubit,
                target_qubit,
                num_qubits,
            )
            expected = cnot_einsum_reference(
                statevector,
                control_qubit,
                target_qubit,
                num_qubits,
            )
            np.testing.assert_allclose(actual, expected, atol=1e-12)


@pytest.mark.parametrize(
    ("basis_index", "expected_index"),
    [
        (4, 4),  # |100>: Control q0 ist 0, daher bleibt das Target q1 gleich.
        (5, 7),  # |101>: Control q0 ist 1, daher wird Target q1 gekippt.
    ],
)
def test_cnot_respects_control_bit(
    basis_index: int,
    expected_index: int,
) -> None:
    """CNOT changes the target exactly when the control bit is one."""
    statevector = np.zeros(8, dtype=complex)
    statevector[basis_index] = 1

    result = apply_cnot_statevector(
        statevector,
        control_qubit=0,
        target_qubit=1,
        num_qubits=3,
    )

    expected = np.zeros(8, dtype=complex)
    expected[expected_index] = 1
    np.testing.assert_array_equal(result, expected)


def test_cnot_does_not_modify_input_statevector() -> None:
    """The CNOT implementation writes its permutation into a new array."""
    statevector = np.arange(8, dtype=complex)
    original = statevector.copy()

    apply_cnot_statevector(statevector, 2, 0, 3)

    np.testing.assert_array_equal(statevector, original)


def test_cnot_tensor_wrapper_preserves_shape_and_order() -> None:
    """The CNOT wrapper accepts and returns the simulator tensor format."""
    statevector = np.arange(16, dtype=complex)
    tensor = np.reshape(statevector, (2, 2, 2, 2), order="F")

    result = apply_cnot_gate(tensor, 3, 1, 4)
    expected = cnot_einsum_reference(statevector, 3, 1, 4)

    assert result.shape == tensor.shape
    np.testing.assert_array_equal(
        np.reshape(result, -1, order="F"),
        expected,
    )


@pytest.mark.parametrize(
    ("control_qubit", "target_qubit", "num_qubits"),
    [
        (0, 0, 2),
        (-1, 1, 2),
        (0, 2, 2),
        (0, 1, 1),
    ],
)
def test_cnot_rejects_invalid_qubit_arguments(
    control_qubit: int,
    target_qubit: int,
    num_qubits: int,
) -> None:
    """Control and target must be distinct valid qubits."""
    statevector = np.zeros(2**num_qubits, dtype=complex)

    with pytest.raises(ValueError):
        apply_cnot_statevector(
            statevector,
            control_qubit,
            target_qubit,
            num_qubits,
        )
