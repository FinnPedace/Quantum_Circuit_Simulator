Architektur
===========

Paketstruktur
-------------

Das Projekt verwendet ein ``src``-Layout:

.. code-block:: text

   src/quantum_circuit_simulator/
   ├── __init__.py             öffentliche Exporte
   ├── api.py                  Einstiegspunkt simulate()
   ├── config.py               SimulationConfig
   ├── result.py               SimulationResult
   ├── simulator.py            eigener StatevectorSimulator
   ├── aer_simulator.py        Aer-Referenzwrapper
   ├── alt_numpy_einsum.py     alternative Ein-Qubit-Referenz
   └── visualization.py        Matplotlib-Ausgabe

Datenfluss
-----------------------

.. code-block:: text

   QuantumCircuit
         │
         ▼
   simulate(circuit, config)
         │
         ├── config is None → SimulationConfig()
         │
         ▼
   StatevectorSimulator.simulate(...)
         │
         ├── Circuit validieren
         ├── |0...0> initialisieren
         ├── Gates und Fusion-Gruppen ausführen
         ├── optional Counts samplen
         │
         ▼
   SimulationResult(statevector, counts)

Die öffentliche Funktion in ``api.py`` instanziiert aktuell immer den eigenen
:class:`~quantum_circuit_simulator.simulator.StatevectorSimulator`. Der
:class:`~quantum_circuit_simulator.aer_simulator.AerSimulatorWrapper` ist noch
im Paket vorhanden, wird aber nicht von :func:`quantum_circuit_simulator.simulate`
aufgerufen.

Konfigurations- und Ergebnisobjekte
-----------------------------------

:class:`~quantum_circuit_simulator.SimulationConfig` und
:class:`~quantum_circuit_simulator.SimulationResult` sind eingefrorene
Dataclasses. Ihre Felder können nach der Konstruktion nicht neu zugewiesen
werden.

Interne Darstellungen
---------------------

Der Simulator verwendet während der Gate-Ausführung einen Tensor der Form
``(2,) * num_qubits``. Vor und nach der Gate-Schleife wird zwischen diesem
Tensor und einem flachen Statevector umgeformt:

.. code-block:: python

   tensor = np.reshape(state, (2,) * num_qubits, order="F")
   final_sv = np.reshape(tensor, -1, order="F")

Die Fortran-Ordnung ist Teil der fachlichen Konvention: Tensorachse ``i``
entspricht Qiskit-Qubit ``i``. Ohne ``order="F"`` würden Gate-Ziel und
Bitposition nicht mehr übereinstimmen.

Zentrale Komponenten
-----------------------------

``api.py``
   Stellt die öffentlich nutzbaren Funktionen des Simulators bereit.

``simulator.py``
   Validiert den Circuit, verwaltet Gate Fusion, kontrahiert Ein-Qubit- und
   CNOT-Matrizen und erzeugt Counts.

``alt_numpy_einsum.py``
   Implementiert Ein-Qubit- und CNOT-Operationen über Numba-kompilierte
   Indexpaarung auf einem flachen Statevector. Der ``numba``-Backendpfad des
   ``StatevectorSimulator`` verwendet diese Funktionen.

``aer_simulator.py``
   Delegiert Statevector und Counts an Qiskit Aer. Die Tests nutzen Aer direkt
   als unabhängige Referenz.

``visualization.py``
   Visualisiert den Circuit und das Resultat.

Python-Pakete
--------------

NumPy
   Zustandsarrays, Matrizen, Tensor-Kontraktion, Wahrscheinlichkeiten und
   Zufallssampling.

Numba
   JIT-Kompilierung der expliziten Ein-Qubit- und CNOT-Blockschleifen zu
   nativem Maschinencode.

Qiskit
   Circuit-Datenmodell, Operationen und Matrixdarstellungen.

Qiskit Aer
   Referenzsimulation und Test-Oracle; nicht Teil des öffentlichen
   Ausführungspfads.

Matplotlib
   Optionale grafische Darstellung eines Resultats.
