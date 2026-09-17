Schnellstart
============

Öffentliche Schnittstelle
-------------------------

Für normale Anwendungen reichen die vier Exporte des Hauptpakets:

.. code-block:: python

   from quantum_circuit_simulator import (
       SimulationConfig,
       SimulationResult,
       plot_simulation_result,
       simulate,
   )

Die Funktion :func:`quantum_circuit_simulator.simulate` nimmt einen
:class:`qiskit.QuantumCircuit` und optional eine
:class:`~quantum_circuit_simulator.SimulationConfig` entgegen. Sie liefert ein
:class:`~quantum_circuit_simulator.SimulationResult`.

Simulation ohne Messung
-----------------------

.. code-block:: python

   import numpy as np
   from qiskit import QuantumCircuit
   from quantum_circuit_simulator import simulate

   circuit = QuantumCircuit(1)
   circuit.h(0)

   result = simulate(circuit)

   print(result.statevector)
   # ungefähr: [0.70710678+0.j, 0.70710678+0.j]
   assert np.allclose(np.abs(result.statevector) ** 2, [0.5, 0.5])
   assert result.counts is None

Ohne Classical Bits wird nicht gesampelt und ``counts`` bleibt ``None``.

Simulation mit Endmessung
-------------------------

.. code-block:: python

   from qiskit import QuantumCircuit
   from quantum_circuit_simulator import SimulationConfig, simulate

   circuit = QuantumCircuit(2)
   circuit.h(0)
   circuit.cx(0, 1)
   circuit.measure_all()

   config = SimulationConfig(shots=2_000, seed=7)
   result = simulate(circuit, config)

   print(result.statevector)
   print(result.counts)

``shots`` legt die Stichprobengröße fest. ``seed`` initialisiert den
NumPy-Zufallszahlengenerator und macht die Counts für dieselbe Umgebung und
dieselben Eingaben reproduzierbar.

Das Resultat verstehen
----------------------

``statevector``
   Ein komplexes NumPy-Array der Länge :math:`2^n`. Es beschreibt den exakten
   Zustand nach allen Gates und vor den abschließenden Messungen.

``counts``
   Entweder ``None`` oder ein Dictionary von Bitstrings auf Häufigkeiten, zum
   Beispiel ``{"00": 1013, "11": 987}``. Die Summe der Werte entspricht
   ``shots``.

Qiskit-Basisordnung
-------------------

Der Statevector verwendet Qiskits Little-Endian-Konvention. Für drei Qubits
wird der Basiszustand als

.. math::

   |q_2 q_1 q_0\rangle

angezeigt. Qubit ``q0`` ist das niederwertigste Bit. Der Vektorindex 1 gehört
also zu ``|001>`` und der Index 4 zu ``|100>``.

Eigene Ein-Qubit-Matrix
-----------------------

Jede Qiskit-Operation, deren ``to_matrix()`` eine 2×2-Matrix liefert, kann
verwendet werden. Dazu zählen auch selbst definierte ``UnitaryGate``-Objekte:

.. code-block:: python

   import numpy as np
   from qiskit import QuantumCircuit
   from qiskit.circuit.library import UnitaryGate
   from quantum_circuit_simulator import simulate

   matrix = np.array([[0, 1j], [1j, 0]], dtype=complex)
   circuit = QuantumCircuit(1)
   circuit.append(UnitaryGate(matrix), [0])

   result = simulate(circuit)
   print(result.statevector)

Fehler behandeln
----------------

Nicht unterstützte Circuit-Strukturen lösen derzeit
:class:`NotImplementedError` aus:

.. code-block:: python

   try:
       result = simulate(circuit)
   except NotImplementedError as error:
       print(f"Circuit wird nicht unterstützt: {error}")

Welche Strukturen zulässig sind, beschreibt :doc:`supported_operations`.
