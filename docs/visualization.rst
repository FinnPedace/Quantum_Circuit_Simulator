Visualisierung
==============

Die Funktion :func:`quantum_circuit_simulator.plot_simulation_result` stellt
drei Aspekte einer Simulation in einer Matplotlib-Figure dar:

1. den eingegebenen Circuit als schematische Zeichnung,
2. Amplituden und Wahrscheinlichkeiten des Statevectors,
3. die gesampelten Measurement Counts.

Beispiel
--------

.. code-block:: python

   from qiskit import QuantumCircuit
   from quantum_circuit_simulator import (
       SimulationConfig,
       plot_simulation_result,
       simulate,
   )

   circuit = QuantumCircuit(2)
   circuit.h(0)
   circuit.cx(0, 1)
   circuit.measure_all()

   result = simulate(circuit, SimulationConfig(shots=1_000, seed=42))
   figure = plot_simulation_result(circuit, result)

Standardmäßig ruft die Funktion ``matplotlib.pyplot.show()`` auf. In Tests,
Notebooks oder beim Speichern kann die Anzeige deaktiviert werden:

.. code-block:: python

   figure = plot_simulation_result(circuit, result, show=False)
   figure.savefig("bell_result.png", dpi=150)

Rückgabewert
------------

Die Funktion gibt immer die erzeugte :class:`matplotlib.figure.Figure` zurück.
Damit können bei Bedarf Achsen, Beschriftungen und Ausgabeformat nachträglich angepasst
werden.
