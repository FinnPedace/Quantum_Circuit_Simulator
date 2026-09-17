API-Referenz
============

Öffentliche API
---------------

Die folgenden Namen werden direkt aus ``quantum_circuit_simulator``
exportiert.

Simulation
~~~~~~~~~~

.. autofunction:: quantum_circuit_simulator.simulate

Konfiguration
~~~~~~~~~~~~~

.. autoclass:: quantum_circuit_simulator.SimulationConfig
   :members:

Ergebnis
~~~~~~~~

.. autoclass:: quantum_circuit_simulator.SimulationResult
   :members:

Visualisierung
~~~~~~~~~~~~~~

.. autofunction:: quantum_circuit_simulator.plot_simulation_result

Interne Simulatoren
-------------------

Diese Klassen gehören nicht zu den Exporten des Hauptpakets. Sie werden für
Implementierungsdetails, Tests und Referenzvergleiche dokumentiert.

.. autoclass:: quantum_circuit_simulator.simulator.StatevectorSimulator
   :members: simulate

.. autoclass:: quantum_circuit_simulator.aer_simulator.AerSimulatorWrapper
   :members: simulate

Alternative Ein-Qubit-Funktionen
--------------------------------

.. autofunction:: quantum_circuit_simulator.alt_numpy_einsum.apply_single_qubit_unitary

.. autofunction:: quantum_circuit_simulator.alt_numpy_einsum.apply_single_qubit_gate
