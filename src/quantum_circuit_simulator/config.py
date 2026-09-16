from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    shots: int = 1024
    seed: int | None = None
