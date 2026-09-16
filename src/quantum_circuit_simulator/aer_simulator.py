from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from .config import SimulationConfig
from .result import SimulationResult

class AerSimulatorWrapper:
    def simulate(self, circuit: QuantumCircuit, config: SimulationConfig) -> SimulationResult:
        # 1. Statevector vor der Messung extrahieren
        sv_circ = circuit.remove_final_measurements(inplace=False)
        sv_circ.save_statevector()
        
        aer = AerSimulator(method="statevector", seed_simulator=config.seed)
        sv_data = aer.run(sv_circ, shots=1).result().get_statevector().data

        # 2. Counts generieren (falls Messungen existieren)
        counts = None
        if circuit.num_clbits > 0:
            counts_data = aer.run(circuit, shots=config.shots, seed_simulator=config.seed).result()
            counts = counts_data.get_counts()

        return SimulationResult(statevector=sv_data, counts=counts)