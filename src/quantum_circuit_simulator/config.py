from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    """Konfiguration einer Simulation.

    :param shots: Anzahl der Samples für Measurement Counts.
    :param seed: Optionaler Seed des NumPy-Zufallszahlengenerators.
    """

    shots: int = 1024
    seed: int | None = None
