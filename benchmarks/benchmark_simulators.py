"""End-to-end benchmark for Aer and all custom simulator variants.

Run from the project root, for example:

    uv run python benchmarks/benchmark_simulators.py --qubits 14 --layers 8

Numba compilation is performed during warm-up and is not part of the reported
timings. Every implementation is checked against Aer's statevector first.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import platform
from statistics import median
from time import perf_counter

import numba
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quantum_circuit_simulator.config import SimulationConfig
from quantum_circuit_simulator.result import SimulationResult
from quantum_circuit_simulator.simulator import StatevectorSimulator

Runner = Callable[[], SimulationResult]


def build_benchmark_circuit(num_qubits: int, layers: int) -> QuantumCircuit:
    """Build a deterministic circuit containing fusion groups and CNOTs."""
    if num_qubits < 2:
        raise ValueError("num_qubits must be at least 2")
    if layers < 1:
        raise ValueError("layers must be at least 1")

    circuit = QuantumCircuit(num_qubits)
    for layer in range(layers):
        for qubit in range(num_qubits):
            angle = (layer + 1) * (qubit + 1) / (num_qubits * layers)
            # These consecutive gates form one useful fusion group per qubit.
            circuit.rx(angle, qubit)
            circuit.ry(-angle / 2, qubit)
            circuit.rz(angle / 3, qubit)

        control = layer % num_qubits
        target = (layer + 1) % num_qubits
        circuit.cx(control, target)

    return circuit


def statevectors_equivalent(
    actual: np.ndarray,
    expected: np.ndarray,
    *,
    atol: float = 1e-11,
) -> bool:
    """Compare statevectors while allowing a global phase."""
    nonzero = np.flatnonzero(np.abs(expected) > atol)
    if nonzero.size == 0:
        return bool(np.allclose(actual, expected, atol=atol))
    pivot = nonzero[0]
    phase = actual[pivot] / expected[pivot]
    return bool(
        np.isclose(np.abs(phase), 1.0, atol=atol)
        and np.allclose(actual, phase * expected, atol=atol)
    )


def measure_runner(runner: Runner, repeats: int) -> list[float]:
    """Measure complete simulation calls with a high-resolution clock."""
    durations = []
    for _ in range(repeats):
        start = perf_counter()
        runner()
        durations.append(perf_counter() - start)
    return durations


def format_table(
    timings: dict[str, list[float]],
    aer_name: str,
    baseline_name: str,
) -> str:
    """Return an aligned benchmark table with two relative speedups."""
    medians = {name: median(values) for name, values in timings.items()}
    aer_time = medians[aer_name]
    baseline_time = medians[baseline_name]
    rows = [
        (
            name,
            f"{medians[name] * 1_000:.3f}",
            f"{min(values) * 1_000:.3f}",
            f"{aer_time / medians[name]:.2f}x",
            f"{baseline_time / medians[name]:.2f}x",
        )
        for name, values in timings.items()
    ]
    headers = (
        "Simulator",
        "Median [ms]",
        "Best [ms]",
        "Speedup vs Aer",
        "Speedup vs einsum/no fusion",
    )
    widths = [
        max(len(headers[column]), *(len(row[column]) for row in rows))
        for column in range(len(headers))
    ]

    def render(row: tuple[str, ...]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join([render(headers), separator, *(render(row) for row in rows)])


def collect_benchmark(
    num_qubits: int,
    layers: int,
    repeats: int,
    warmups: int,
) -> tuple[QuantumCircuit, dict[str, list[float]]]:
    """Validate and measure all variants for one circuit size."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if warmups < 1:
        raise ValueError("warmups must be at least 1")

    circuit = build_benchmark_circuit(num_qubits, layers)
    config = SimulationConfig(shots=1, seed=42)

    # Construct the Aer backend and its save instruction once, just like the
    # custom simulator objects below. Object construction is not benchmarked.
    aer = AerSimulator(method="statevector", seed_simulator=config.seed)
    aer_circuit = circuit.copy()
    aer_circuit.save_statevector()

    def run_aer() -> SimulationResult:
        aer_result = aer.run(aer_circuit, shots=1).result()
        statevector = np.asarray(aer_result.get_statevector().data)
        return SimulationResult(statevector=statevector, counts=None)

    simulators = {
        "einsum / no fusion": StatevectorSimulator(backend="einsum", gate_fusion=False),
        "einsum / fusion": StatevectorSimulator(backend="einsum", gate_fusion=True),
        "numba / no fusion": StatevectorSimulator(backend="numba", gate_fusion=False),
        "numba / fusion": StatevectorSimulator(backend="numba", gate_fusion=True),
    }
    runners: dict[str, Runner] = {
        "AerSimulator": run_aer,
        **{
            name: lambda simulator=simulator: simulator.simulate(circuit, config)
            for name, simulator in simulators.items()
        },
    }

    # Warm-up excludes Numba JIT compilation and one-time backend setup from
    # the measured steady-state performance.
    warm_results: dict[str, SimulationResult] = {}
    for name, runner in runners.items():
        for _ in range(warmups):
            warm_results[name] = runner()

    reference = warm_results["AerSimulator"].statevector
    for name, result in warm_results.items():
        if not statevectors_equivalent(result.statevector, reference):
            raise RuntimeError(f"{name} does not match the Aer statevector")

    timings = {
        name: measure_runner(runner, repeats) for name, runner in runners.items()
    }

    return circuit, timings


def run_benchmark(
    num_qubits: int,
    layers: int,
    repeats: int,
    warmups: int,
) -> None:
    """Validate, warm up, time, and print all simulator variants."""
    circuit, timings = collect_benchmark(
        num_qubits=num_qubits,
        layers=layers,
        repeats=repeats,
        warmups=warmups,
    )

    print(
        f"Python {platform.python_version()}, NumPy {np.__version__}, "
        f"Numba {numba.__version__}"
    )
    print(
        f"Circuit: {num_qubits} qubits, {layers} layers, "
        f"{len(circuit.data)} gates; {repeats} measured repetitions"
    )
    print()
    print(
        format_table(
            timings,
            aer_name="AerSimulator",
            baseline_name="einsum / no fusion",
        )
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line settings for a reproducible benchmark run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qubits", type=int, default=14)
    parser.add_argument("--layers", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_benchmark(
        num_qubits=arguments.qubits,
        layers=arguments.layers,
        repeats=arguments.repeats,
        warmups=arguments.warmups,
    )
