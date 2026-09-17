"""End-to-end benchmark for Aer and all custom simulator variants.

Run from the project root, for example:

    uv run python benchmarks/benchmark_simulators.py --qubits 14 --gates 100

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


def build_random_benchmark_circuit(
    num_qubits: int,
    gate_count: int,
    seed: int,
) -> QuantumCircuit:
    """Build a reproducible random circuit from the supported gate set."""
    if num_qubits < 2:
        raise ValueError("num_qubits must be at least 2")
    if gate_count < 1:
        raise ValueError("gate_count must be at least 1")

    random_generator = np.random.default_rng(seed)
    circuit = QuantumCircuit(num_qubits)
    single_qubit_gates = ("h", "x", "sx", "rx", "ry", "rz")

    for _ in range(gate_count):
        # Most operations are single-qubit gates. CNOTs occur often enough to
        # create realistic fusion boundaries without dominating the circuit.
        if random_generator.random() < 0.8:
            target = int(random_generator.integers(num_qubits))
            gate_name = str(random_generator.choice(single_qubit_gates))
            if gate_name in ("rx", "ry", "rz"):
                angle = float(random_generator.uniform(-np.pi, np.pi))
                getattr(circuit, gate_name)(angle, target)
            else:
                getattr(circuit, gate_name)(target)
            continue

        control, target = random_generator.choice(
            num_qubits,
            size=2,
            replace=False,
        )
        circuit.cx(int(control), int(target))

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
    gate_count: int,
    repeats: int,
    warmups: int,
    seed: int,
) -> tuple[QuantumCircuit, dict[str, list[float]]]:
    """Validate and measure all variants for one circuit size."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if warmups < 1:
        raise ValueError("warmups must be at least 1")

    circuit = build_random_benchmark_circuit(
        num_qubits,
        gate_count,
        seed,
    )
    config = SimulationConfig(shots=1, seed=seed)

    # Use Aer as a deliberately unoptimized reference: its internal gate
    # fusion is disabled and one worker thread prevents parallel statevector
    # updates. Object construction is not part of the measured runtime.
    aer = AerSimulator(
        method="statevector",
        fusion_enable=False,
        max_parallel_threads=1,
        max_parallel_experiments=1,
        max_parallel_shots=1,
        seed_simulator=config.seed,
    )
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
    gate_count: int,
    repeats: int,
    warmups: int,
    seed: int,
) -> None:
    """Validate, warm up, time, and print all simulator variants."""
    circuit, timings = collect_benchmark(
        num_qubits=num_qubits,
        gate_count=gate_count,
        repeats=repeats,
        warmups=warmups,
        seed=seed,
    )

    print(
        f"Python {platform.python_version()}, NumPy {np.__version__}, "
        f"Numba {numba.__version__}"
    )
    print(
        f"Circuit: {num_qubits} qubits, {len(circuit.data)} random gates, "
        f"seed {seed}; {repeats} measured repetitions"
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
    parser.add_argument("--gates", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_benchmark(
        num_qubits=arguments.qubits,
        gate_count=arguments.gates,
        repeats=arguments.repeats,
        warmups=arguments.warmups,
        seed=arguments.seed,
    )
