from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class SimulationResult:
    statevector: np.ndarray
    counts: dict[str, int] | None