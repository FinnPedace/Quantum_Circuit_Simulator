from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class SimulationResult:
    """Ergebnis einer Circuit-Simulation.

    :param statevector: Komplexer Zustand nach allen Gates und vor Messungen.
    :param counts: Gesampelte Bitstring-Häufigkeiten oder ``None``.
    """

    statevector: np.ndarray
    counts: dict[str, int] | None
