Quantum Circuit Simulator
=========================

Der Quantum Circuit Simulator ist eine kleine Python-Bibliothek zur
Statevector-Simulation von :class:`qiskit.QuantumCircuit`-Objekten. Der eigene
Simulator verarbeitet allgemeine Ein-Qubit-Matrizen und CNOT-Gates, fusioniert
aufeinanderfolgende Ein-Qubit-Gates und kann abschließende Messungen aus dem
berechneten Statevector samplen. Intern stehen NumPy-``einsum`` und
Numba-kompilierte Blockschleifen als numerische Backends zur Verfügung.

Die Bibliothek ist vor allem als nachvollziehbare Implementierung gedacht:
Tensorkontraktion, Gate Fusion, CNOT-Kontraktion und Measurement Sampling sind im
Quellcode getrennt erkennbar und werden gegen Qiskit Aer getestet.

Ein kleines Beispiel
----------------------

.. code-block:: python

   from qiskit import QuantumCircuit
   from quantum_circuit_simulator import SimulationConfig, simulate

   circuit = QuantumCircuit(2)
   circuit.h(0)
   circuit.cx(0, 1)
   circuit.measure_all()

   result = simulate(
       circuit,
       SimulationConfig(shots=1_000, seed=42),
   )

   print(result.statevector)
   print(result.counts)

Der zurückgegebene Statevector beschreibt immer den Zustand vor den
Endmessungen. 

.. note::

   Unterstützt werden Ein-Qubit-Operationen mit einer 2×2-Matrix, ``cx``, Barrieren und
   vollständige Endmessungen. Die genauen Limitierungen stehen unter
   :doc:`supported_operations`.

.. toctree::
   :maxdepth: 2
   :caption: Benutzung

   installation
   quickstart
   supported_operations
   visualization

.. toctree::
   :maxdepth: 2
   :caption: Implementierung

   architecture
   simulation
   gate_fusion
   alternative_einsum

.. toctree::
   :maxdepth: 2
   :caption: Referenz und Entwicklung

   api
   testing
   benchmarks
