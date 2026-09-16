from qiskit import QuantumCircuit
from .config import SimulationConfig
from .result import SimulationResult
from .aer_simulator import AerSimulatorWrapper

def simulate(circuit: QuantumCircuit, config: SimulationConfig | None = None) -> SimulationResult:
    if config is None:
        config = SimulationConfig()
        
    # Für Phase 1 leiten wir an den AerSimulatorWrapper weiter
    simulator = AerSimulatorWrapper()
    return simulator.simulate(circuit, config)