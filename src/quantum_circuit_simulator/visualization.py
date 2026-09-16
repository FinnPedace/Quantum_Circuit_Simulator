"""Plots for inspecting a circuit simulation result."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from qiskit import QuantumCircuit

from .result import SimulationResult


def plot_simulation_result(
    circuit: QuantumCircuit,
    result: SimulationResult,
    *,
    show: bool = True,
) -> Figure:
    """Plot the input circuit, statevector probabilities, and measurement counts.

    The statevector is shown before measurement. Set ``show=False`` when the
    returned figure should be embedded elsewhere or inspected in a test.
    """
    num_qubits = circuit.num_qubits
    basis_labels = [
        f"|{format(index, f'0{num_qubits}b')}>"
        for index in range(len(result.statevector))
    ]
    probabilities = np.abs(result.statevector) ** 2

    figure, (circuit_axis, state_axis, counts_axis) = plt.subplots(
        3,
        1,
        figsize=(max(8, len(basis_labels) * 0.8), 10),
        layout="constrained",
    )

    circuit_axis.axis("off")
    circuit_axis.set_title("Input circuit")
    circuit_axis.text(
        0.5,
        0.5,
        str(circuit.draw(output="text")),
        fontfamily="monospace",
        ha="center",
        va="center",
    )

    state_positions = np.arange(len(basis_labels))
    state_axis.bar(state_positions, probabilities, color="tab:blue")
    state_axis.set_title("Statevector probabilities before measurement")
    state_axis.set_ylabel(r"$|c_x|^2$")
    state_axis.set_xticks(state_positions, basis_labels)
    state_axis.set_ylim(0, max(1.0, float(probabilities.max()) * 1.15))
    for position, amplitude, probability in zip(
        state_positions,
        result.statevector,
        probabilities,
        strict=True,
    ):
        state_axis.annotate(
            f"{amplitude.real:.3g}{amplitude.imag:+.3g}j\np={probability:.3g}",
            (position, probability),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    counts_axis.set_title("Measurement counts")
    counts_axis.set_ylabel("Shots")
    if result.counts is None:
        counts_axis.axis("off")
        counts_axis.text(
            0.5,
            0.5,
            "No final measurements in the circuit.",
            ha="center",
            va="center",
        )
    else:
        count_labels = sorted(result.counts)
        count_values = [result.counts[label] for label in count_labels]
        count_positions = np.arange(len(count_labels))
        counts_axis.bar(count_positions, count_values, color="tab:orange")
        counts_axis.set_xticks(count_positions, count_labels)
        for position, count in zip(count_positions, count_values, strict=True):
            counts_axis.annotate(
                str(count),
                (position, count),
                ha="center",
                va="bottom",
            )

    if show:
        plt.show()

    return figure
