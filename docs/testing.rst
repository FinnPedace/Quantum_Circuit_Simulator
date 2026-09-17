Tests und Qualitätssicherung
============================

Tests ausführen
---------------

Die komplette Suite wird aus dem Projektverzeichnis gestartet:

.. code-block:: console

   uv run pytest

Eine einzelne Testdatei kann gezielt ausgeführt werden:

.. code-block:: console

   uv run pytest tests/test_gate_fusion.py -q

Testgruppen
-----------

``test_aer_simulator.py``
   Contract-Tests der öffentlichen ``simulate()``-API. Ein-Qubit-Gates,
   benutzerdefinierte Unitaries, CNOT, Bell-Zustand, Counts und ein zufälliger
   unterstützter Circuit werden mit Qiskit Aer verglichen.

``test_gate_fusion.py``
   Prüft Matrixreihenfolge, Gruppierung unabhängiger Qubits, Fusionsgrenzen an
   CNOT und einen längeren Circuit mit mehreren Fusion-Gruppen.

``test_alt_numpy_einsum.py``
   Vergleicht die explizite Blockschleife für verschiedene Qubitzahlen und
   alle möglichen Ziel-Qubits mit der bestehenden ``np.einsum``-Konvention.
   Für CNOT werden sämtliche geordneten Control-/Target-Kombinationen geprüft.
   Zusätzlich werden konkrete Indexpaarung, Control-Semantik, unveränderte
   Eingaben, ungültige Argumente und beide Tensoradapter getestet.

``test_visualization.py``
   Verwendet das nicht-interaktive Matplotlib-Backend ``Agg`` und kontrolliert
   Aufbau und Titel der drei Visualisierungsachsen.

``test_simulator_backends.py``
   Prüft alle vier Kombinationen aus ``einsum``/``numba`` und Gate Fusion
   an/aus gegen Aer. Außerdem wird kontrolliert, dass das Abschalten der Fusion
   wirklich jede Ein-Qubit-Matrix einzeln anwendet.

Statevector-Vergleich
---------------------

Zwei physikalisch äquivalente Statevectoren können sich um eine globale Phase
:math:`e^{i\phi}` unterscheiden. Die Aer-Tests suchen deshalb zunächst eine
nichtverschwindende Referenzamplitude, bestimmen daraus den Phasenfaktor und
vergleichen anschließend

.. math::

   |\psi_\text{actual}\rangle
   \approx e^{i\phi}|\psi_\text{expected}\rangle.

Eine absolute Toleranz von ungefähr ``1e-12`` fängt normale
Gleitkomma-Rundungsreste ab.

Counts testen
-------------

Deterministische Circuits werden exakt geprüft. Beim Bell-Zustand wird
kontrolliert, dass nur ``00`` und ``11`` auftreten und die Summe der Counts der
Shotzahl entspricht. Zufällige Counts verschiedener Simulatoren sollten nicht
blind Eintrag für Eintrag verglichen werden, weil unterschiedliche
Zufallszahlengeneratoren trotz gleicher Verteilung andere Samples liefern
können.

Dokumentation prüfen
--------------------

Warnungen sollten beim Sphinx-Build als Fehler behandelt werden:

.. code-block:: console

   uv run sphinx-build -W --keep-going -b html docs docs/_build/html

Damit werden unter anderem ungültige Querverweise, fehlerhafte RST-Strukturen
und Probleme beim Import der API sichtbar.

Neue Funktionalität absichern
-----------------------------

Bei neuen Gates oder Backends sollten mindestens folgende Eigenschaften
getestet werden:

* Abgleich des Statevectors mit einer unabhängigen Aer-Referenz;
* alle zulässigen Ziel-Qubit-Positionen, nicht nur ``q0``;
* Circuit-Grenzen wie CNOT, Barriere und Messung;
* ungültige Eingaben und erwarteter Fehlertyp;
* unveränderte öffentliche Semantik von ``SimulationResult``;
* bei Optimierungen zusätzlich ein separater Benchmark außerhalb der
  Korrektheitstests.
