import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit

from quantum_circuit_simulator.api import simulate
from quantum_circuit_simulator.config import SimulationConfig
from quantum_circuit_simulator.visualization import plot_simulation_result


def test_plot_simulation_result_contains_circuit_statevector_and_counts() -> None:
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.measure_all()
    result = simulate(circuit, SimulationConfig(shots=10, seed=42))

    figure = plot_simulation_result(circuit, result, show=False)

    assert len(figure.axes) == 3
    assert figure.axes[0].get_title() == "Input circuit"
    assert figure.axes[1].get_title() == "Statevector probabilities before measurement"
    assert figure.axes[2].get_title() == "Measurement counts"

    plt.close(figure)
