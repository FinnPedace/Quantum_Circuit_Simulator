Unterstützte Operationen und Grenzen
====================================

Unterstützte Circuit-Bestandteile
---------------------------------

Der eigene Simulator akzeptiert aktuell:

Ein-Qubit-Gates
   Eine Operation wird akzeptiert, wenn sie ``to_matrix()`` anbietet und die
   zurückgegebene Matrix die Form ``(2, 2)`` besitzt.

``cx``
   CNOT ist das einzige explizit implementierte Zwei-Qubit-Gate.

``barrier``
   Eine Barriere verändert den Zustand nicht, beendet aber eine laufende
   Gate-Fusion-Gruppe.

Vollständige Endmessungen
   Messungen sind nur am Circuit-Ende erlaubt. Sobald die erste Messung
   aufgetreten ist, darf kein Gate mehr folgen. Wenn gemessen wird, müssen alle
   Qubits gemessen werden.

Nicht unterstützt
-----------------

Unter anderem werden abgelehnt:

* andere Zwei- oder Mehr-Qubit-Gates wie ``cz``, ``swap`` oder ``ccx``;
* Teilmessungen;
* Gates nach der ersten Messung;
* mehrere Classical Registers;
* Reset, Noise-Modelle und nicht-unitäre Kanäle;
* dynamische Circuits;
* beliebige Initialzustände -- die Simulation startet immer in
  :math:`|0\ldots0\rangle`.

Messzuordnung
-------------

Für verlässliche Qiskit-kompatible Counts sollte der Circuit mit
``circuit.measure_all()`` abgeschlossen werden. Der aktuelle Sampler formatiert
den gezogenen Basisindex direkt als Bitstring. Eine beliebige Zuordnung von
Qubits zu Classical Bits wird nicht ausgewertet.

Technisch startet das Sampling momentan, sobald der Circuit Classical Bits
besitzt. Ein Circuit mit Classical Bits, aber ohne ``measure``-Anweisung kann
daher ebenfalls Counts erzeugen. Anwendungen sollten sich nicht auf dieses
Implementierungsdetail verlassen, sondern entweder keine Classical Bits
anlegen oder ``measure_all()`` verwenden.

Konfiguration
-------------

``SimulationConfig`` besitzt zwei Felder:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Feld
     - Standard
     - Bedeutung
   * - ``shots``
     - ``1024``
     - Anzahl der Samples für Circuits mit Classical Bits. Es sollte eine
       positive ganze Zahl sein.
   * - ``seed``
     - ``None``
     - Seed des NumPy-Zufallszahlengenerators. ``None`` verwendet einen nicht
       festgelegten Seed.

Die Dataclass selbst prüft die Werte derzeit nicht. Ungeeignete Werte, etwa
negative ``shots``, führen erst beim NumPy-Sampling zu einem Fehler.
