from qiskit import QuantumCircuit
from .config import SimulationConfig
from .result import SimulationResult
from .aer_simulator import AerSimulatorWrapper
from .simulator import StatevectorSimulator


def simulate(
    circuit: QuantumCircuit, config: SimulationConfig | None = None
) -> SimulationResult:
    """Simuliere einen unterstützten Qiskit-Circuit.

    Der eigene Statevector-Simulator startet in ``|0...0>`` und gibt den
    Zustand nach allen Gates, aber vor abschließenden Messungen zurück. Besitzt
    der Circuit Classical Bits, werden zusätzlich Measurement Counts erzeugt.

    :param circuit: Zu simulierender Qiskit-Circuit.
    :param config: Shotzahl und optionaler Zufallsseed. Bei ``None`` wird eine
        Standardkonfiguration verwendet.
    :return: Statevector und optionale Measurement Counts.
    :raises NotImplementedError: Wenn der Circuit eine nicht unterstützte
        Operation oder Messstruktur enthält.
    """
    if config is None:
        config = SimulationConfig()

    # Für Phase 1 leiten wir an den AerSimulatorWrapper weiter
    simulator = (
        StatevectorSimulator()
    )  # Erstellen Sie eine Instanz des StatevectorSimulators
    return simulator.simulate(circuit, config)
