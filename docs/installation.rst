Installation
============

Requirements
------------

The simulator requires Python 3.13 or newer and uses ``uv`` for dependency
management.

Install the project dependencies from the project root::

   uv sync

For development, install the project with its development dependencies::

   uv sync --dev

Usage
-----

The package can then be imported from Python::

   from quantum_circuit_simulator import SimulationConfig, simulate

See the API reference for the available classes and functions.
