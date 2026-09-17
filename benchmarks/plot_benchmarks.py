"""Generate the simulator scaling plot used in the project README.

The script validates every custom result against Aer, excludes Numba JIT
compilation through warm-up calls, writes the median data to CSV, and creates a
PNG plot suitable for GitHub and the Sphinx documentation.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import platform
from statistics import median

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numba
import numpy as np

from benchmark_simulators import collect_benchmark

METHOD_STYLES = {
    "AerSimulator": {
        "color": "#202124",
        "marker": "o",
        "linestyle": "-",
        "linewidth": 2.4,
    },
    "einsum / no fusion": {
        "color": "#e07a1f",
        "marker": "s",
        "linestyle": "--",
        "linewidth": 2.0,
    },
    "einsum / fusion": {
        "color": "#c43d3d",
        "marker": "s",
        "linestyle": "-",
        "linewidth": 2.2,
    },
    "numba / no fusion": {
        "color": "#4c9bd6",
        "marker": "^",
        "linestyle": "--",
        "linewidth": 2.0,
    },
    "numba / fusion": {
        "color": "#1967b3",
        "marker": "^",
        "linestyle": "-",
        "linewidth": 2.5,
    },
}


def collect_scaling_data(
    qubit_counts: list[int],
    layers: int,
    repeats: int,
    warmups: int,
) -> dict[str, list[float]]:
    """Return median runtimes in milliseconds for every method and size."""
    medians_ms = {name: [] for name in METHOD_STYLES}

    for num_qubits in qubit_counts:
        print(f"Benchmarking {num_qubits} qubits ...", flush=True)
        _, timings = collect_benchmark(
            num_qubits=num_qubits,
            layers=layers,
            repeats=repeats,
            warmups=warmups,
        )
        for name in METHOD_STYLES:
            medians_ms[name].append(median(timings[name]) * 1_000)

    return medians_ms


def write_csv(
    output: Path,
    qubit_counts: list[int],
    medians_ms: dict[str, list[float]],
) -> None:
    """Store the plotted median values in a machine-readable CSV file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["qubits", *medians_ms])
        for index, num_qubits in enumerate(qubit_counts):
            writer.writerow(
                [
                    num_qubits,
                    *(f"{medians_ms[name][index]:.6f}" for name in medians_ms),
                ]
            )


def create_plot(
    output: Path,
    qubit_counts: list[int],
    medians_ms: dict[str, list[float]],
    layers: int,
    repeats: int,
) -> None:
    """Create a readable logarithmic scaling plot for the README."""
    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axis = plt.subplots(figsize=(11, 6.5), layout="constrained")

    for name, values in medians_ms.items():
        axis.plot(
            qubit_counts,
            values,
            label=name,
            markersize=7,
            **METHOD_STYLES[name],
        )

    axis.set_yscale("log")
    axis.set_xticks(qubit_counts)
    axis.set_xlabel("Number of qubits")
    axis.set_ylabel("Median simulation time [ms] — logarithmic scale")
    figure.suptitle(
        "Statevector simulator scaling",
        fontsize=18,
        fontweight="bold",
    )
    axis.set_title(
        (
            f"{layers} layers; RX–RY–RZ on every qubit plus one CNOT per layer; "
            f"median of {repeats} warm runs"
        ),
        fontsize=9.5,
        color="#555555",
        pad=12,
    )
    axis.legend(ncols=2, frameon=True, loc="upper left")
    axis.grid(True, which="major", color="#d9d9d9", linewidth=0.8)
    axis.grid(True, which="minor", color="#eeeeee", linewidth=0.5)

    fastest_name = min(medians_ms, key=lambda name: medians_ms[name][-1])
    fastest_value = medians_ms[fastest_name][-1]
    axis.annotate(
        f"Fastest at {qubit_counts[-1]} qubits\n{fastest_name}: {fastest_value:.1f} ms",
        xy=(qubit_counts[-1], fastest_value),
        xytext=(-145, 28),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#555555"},
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#cccccc"},
    )
    figure.text(
        0.995,
        0.003,
        (
            f"Python {platform.python_version()} · NumPy {np.__version__} · "
            f"Numba {numba.__version__} · JIT compilation excluded"
        ),
        ha="right",
        va="bottom",
        fontsize=7.5,
        color="#666666",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, facecolor="white")
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    """Parse plot configuration from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--qubits",
        type=int,
        nargs="+",
        default=[6, 8, 10, 12, 14, 16],
    )
    parser.add_argument("--layers", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/images/benchmark_simulators.png"),
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("benchmarks/results/benchmark_simulators.csv"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    data = collect_scaling_data(
        qubit_counts=arguments.qubits,
        layers=arguments.layers,
        repeats=arguments.repeats,
        warmups=arguments.warmups,
    )
    write_csv(arguments.csv, arguments.qubits, data)
    create_plot(
        arguments.output,
        arguments.qubits,
        data,
        arguments.layers,
        arguments.repeats,
    )
    print(f"Wrote plot to {arguments.output}")
    print(f"Wrote median data to {arguments.csv}")
