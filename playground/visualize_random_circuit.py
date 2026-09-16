"""Run and visualize a reproducible random circuit from the supported gate set."""

import numpy as np
from qiskit import QuantumCircuit

from quantum_circuit_simulator import (
    SimulationConfig,
    plot_simulation_result,
    simulate,
)


def random_supported_circuit(seed: int) -> QuantumCircuit:
    """Create a random circuit containing single-qubit gates and CNOTs only."""
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


circuit = random_supported_circuit(seed=42)
result = simulate(circuit, SimulationConfig(shots=1_000, seed=123))
plot_simulation_result(circuit, result)
