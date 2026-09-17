"""Numba-kompilierte Statevector-Operationen als Alternative zu ``np.einsum``.

Die Python-Wrapper validieren die Eingaben. Die rechenintensiven Blockschleifen
werden von Numba in nativen Maschinencode übersetzt.
"""

import numpy as np
from numba import njit


@njit(cache=True, nogil=True)
def _single_qubit_unitary_kernel(
    statevector: np.ndarray,
    unitary: np.ndarray,
    target_qubit: int,
) -> np.ndarray:
    """Numba-Kernel für die paarweise Ein-Qubit-Matrixmultiplikation."""
    result = np.empty_like(statevector)

    # Die vier Matrixelemente werden nur einmal vor der Schleife gelesen.
    u00 = unitary[0, 0]
    u01 = unitary[0, 1]
    u10 = unitary[1, 0]
    u11 = unitary[1, 1]

    pair_distance = 1 << target_qubit
    block_size = pair_distance << 1

    for block_start in range(0, statevector.size, block_size):
        for offset in range(pair_distance):
            zero_index = block_start + offset
            one_index = zero_index + pair_distance

            # Beide Werte müssen vor dem Schreiben gelesen werden, weil beide
            # neuen Amplituden von beiden alten Amplituden abhängen.
            amplitude_zero = statevector[zero_index]
            amplitude_one = statevector[one_index]

            result[zero_index] = u00 * amplitude_zero + u01 * amplitude_one
            result[one_index] = u10 * amplitude_zero + u11 * amplitude_one

    return result


@njit(cache=True, nogil=True)
def _cnot_kernel(
    statevector: np.ndarray,
    control_qubit: int,
    target_qubit: int,
) -> np.ndarray:
    """Numba-Kernel für die bedingte Permutation der CNOT-Amplituden."""
    result = np.empty_like(statevector)
    pair_distance = 1 << target_qubit
    block_size = pair_distance << 1
    control_bit_mask = 1 << control_qubit

    for block_start in range(0, statevector.size, block_size):
        for offset in range(pair_distance):
            target_zero_index = block_start + offset
            target_one_index = target_zero_index + pair_distance

            if target_zero_index & control_bit_mask:
                # Control = 1: Das Target-Bit wird gekippt, also werden die
                # beiden Amplituden des Target-Paares vertauscht.
                result[target_zero_index] = statevector[target_one_index]
                result[target_one_index] = statevector[target_zero_index]
            else:
                # Control = 0: CNOT wirkt auf dieses Paar wie die Identität.
                result[target_zero_index] = statevector[target_zero_index]
                result[target_one_index] = statevector[target_one_index]

    return result


def apply_single_qubit_unitary(
    statevector: np.ndarray,
    unitary: np.ndarray,
    target_qubit: int,
    num_qubits: int,
) -> np.ndarray:
    """Wende eine 2x2-Matrix auf ein Qubit im flachen Statevector an.

    Die Qubit-Indizes beginnen bei null. Zwei Basiszustände, die sich nur im
    ``target_qubit`` unterscheiden, liegen daher ``2**target_qubit`` Einträge
    auseinander. Für jedes Paar wird folgende Matrixmultiplikation berechnet:

    ``out[zero_index] = U[0, 0] * a0 + U[0, 1] * a1``
    ``out[one_index]  = U[1, 0] * a0 + U[1, 1] * a1``.

    Die Funktion gibt einen neuen Statevector zurück und verändert die Eingabe
    nicht.
    """
    statevector = np.asarray(statevector)
    unitary = np.asarray(unitary)

    if num_qubits < 1:
        raise ValueError("num_qubits must be at least 1")
    if not 0 <= target_qubit < num_qubits:
        raise ValueError(f"target_qubit must be between 0 and {num_qubits - 1}")
    if statevector.ndim != 1:
        raise ValueError("statevector must be one-dimensional")
    expected_size = 1 << num_qubits
    if statevector.size != expected_size:
        raise ValueError(f"statevector must contain {expected_size} amplitudes")
    if unitary.shape != (2, 2):
        raise ValueError("unitary must have shape (2, 2)")

    # Ein gemeinsamer Datentyp verhindert, dass bei einer komplexen Matrix
    # Imaginärteile durch einen reellen Statevector verloren gehen. Zusammen-
    # hängende Arrays halten die Zahl der Numba-Spezialisierungen klein.
    result_dtype = np.result_type(statevector.dtype, unitary.dtype)
    prepared_statevector = np.ascontiguousarray(statevector, dtype=result_dtype)
    prepared_unitary = np.ascontiguousarray(unitary, dtype=result_dtype)
    return _single_qubit_unitary_kernel(
        prepared_statevector,
        prepared_unitary,
        target_qubit,
    )


def apply_cnot_statevector(
    statevector: np.ndarray,
    control_qubit: int,
    target_qubit: int,
    num_qubits: int,
) -> np.ndarray:
    """Wende ein CNOT-Gate auf einen flachen Qiskit-Statevector an.

    Der Statevector wird wie bei der Ein-Qubit-Funktion in Blöcke bezüglich
    des Target-Qubits aufgeteilt. Innerhalb jedes Blocks bilden die Einträge
    mit Target-Bit 0 und 1 jeweils ein Paar. Ist das Control-Bit dieses Paares
    1, werden die beiden Amplituden vertauscht. Bei Control-Bit 0 bleiben sie
    unverändert.

    Die Funktion gibt einen neuen Statevector zurück und verändert die Eingabe
    nicht.
    """
    statevector = np.asarray(statevector)

    if num_qubits < 2:
        raise ValueError("num_qubits must be at least 2 for a CNOT gate")
    if not 0 <= control_qubit < num_qubits:
        raise ValueError(f"control_qubit must be between 0 and {num_qubits - 1}")
    if not 0 <= target_qubit < num_qubits:
        raise ValueError(f"target_qubit must be between 0 and {num_qubits - 1}")
    if control_qubit == target_qubit:
        raise ValueError("control_qubit and target_qubit must be different")
    if statevector.ndim != 1:
        raise ValueError("statevector must be one-dimensional")

    expected_size = 1 << num_qubits
    if statevector.size != expected_size:
        raise ValueError(f"statevector must contain {expected_size} amplitudes")

    # CNOT permutiert nur Amplituden; es ist keine Typ-Promotion nötig.
    prepared_statevector = np.ascontiguousarray(statevector)
    return _cnot_kernel(
        prepared_statevector,
        control_qubit,
        target_qubit,
    )


def apply_single_qubit_gate(
    tensor: np.ndarray,
    matrix: np.ndarray,
    target_qubit: int,
    num_qubits: int,
) -> np.ndarray:
    """Passe die flache Implementierung an das Tensorformat des Simulators an.

    Der Simulator speichert seinen Zustand als Tensor der Form ``(2,) * n``.
    Die eigentliche Paarberechnung erwartet dagegen einen flachen Statevector.
    Diese Funktion formt deshalb Tensor -> Vektor -> Tensor um.
    """
    tensor = np.asarray(tensor)

    # Ein n-Qubit-Zustand hat n Achsen, und jede Achse besitzt die Größe 2.
    expected_shape = (2,) * num_qubits
    if tensor.shape != expected_shape:
        raise ValueError(f"tensor must have shape {expected_shape}")

    # Fortran-Ordnung erhält die im Simulator verwendete Qiskit-Qubitordnung:
    # Tensorachse 0 entspricht dem niederwertigsten Qubit q0.
    statevector = np.reshape(tensor, -1, order="F")

    # Das Gate wird durch die oben implementierte Blockschleife angewendet.
    result = apply_single_qubit_unitary(
        statevector,
        matrix,
        target_qubit,
        num_qubits,
    )

    # Der Simulator erwartet anschließend wieder einen n-dimensionalen Tensor.
    return np.reshape(result, expected_shape, order="F")


def apply_cnot_gate(
    tensor: np.ndarray,
    control_qubit: int,
    target_qubit: int,
    num_qubits: int,
) -> np.ndarray:
    """Passe die flache CNOT-Implementierung an das Tensorformat an.

    Diese Funktion hat dieselbe Aufgabe wie ``apply_single_qubit_gate``: Sie
    formt den Zustandstensor zum flachen Statevector um, führt dort die
    Blockschleife aus und stellt anschließend die ursprüngliche Tensorform
    wieder her.
    """
    tensor = np.asarray(tensor)
    expected_shape = (2,) * num_qubits
    if tensor.shape != expected_shape:
        raise ValueError(f"tensor must have shape {expected_shape}")

    # order="F" erhält die Zuordnung Tensorachse i <-> Qiskit-Qubit i.
    statevector = np.reshape(tensor, -1, order="F")
    result = apply_cnot_statevector(
        statevector,
        control_qubit,
        target_qubit,
        num_qubits,
    )
    return np.reshape(result, expected_shape, order="F")


__all__ = [
    "apply_cnot_gate",
    "apply_cnot_statevector",
    "apply_single_qubit_gate",
    "apply_single_qubit_unitary",
]
