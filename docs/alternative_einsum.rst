Alternative Ein-Qubit-Anwendung
===============================

Zweck und Status
----------------

Das Modul :mod:`quantum_circuit_simulator.alt_numpy_einsum` implementiert die
Anwendung einer 2×2-Matrix ohne ``np.einsum``. Es macht die Bitstruktur eines
Statevectors explizit und dient als Korrektheitsreferenz für spätere
Optimierungen.

.. important::

   Diese Implementierung ist derzeit nicht in den öffentlichen
   Simulationspfad eingebunden. ``simulate()`` verwendet weiterhin die
   ``np.einsum``-Methode aus ``StatevectorSimulator``. Die verschachtelten
   Python-Schleifen sind voraussichtlich langsamer und sind noch kein
   Performance-Backend.

Amplitudenpaare
---------------

Für ein Ziel-Qubit mit nullbasiertem Index :math:`i` unterscheiden sich die
beiden zusammengehörigen Basisindizes um

.. math::

   \text{pair\_distance} = 2^i.

Ein vollständiger Block besteht aus zwei Hälften mit jeweils :math:`2^i`
Einträgen:

.. code-block:: text

   erste Hälfte             zweite Hälfte
   target bit = 0           target bit = 1
   0 ... 2^i-1              2^i ... 2^(i+1)-1

Die Blockgröße beträgt deshalb

.. math::

   \text{block\_size} = 2^{i+1}.

Indexbildung
------------

Die äußere Schleife springt in Schritten von ``block_size`` durch den gesamten
Vektor. Die innere Schleife läuft über die erste Blockhälfte:

.. code-block:: python

   for block_start in range(0, expected_size, block_size):
       for offset in range(pair_distance):
           zero_index = block_start + offset
           one_index = zero_index + pair_distance

``zero_index`` und ``one_index`` besitzen identische Werte für alle anderen
Qubits. Nur das Zielbit ist einmal 0 und einmal 1.

Beispiel für ``n = 3`` und ``i = 1``
-------------------------------------

Hier gelten ``pair_distance = 2`` und ``block_size = 4``:

.. list-table::
   :header-rows: 1

   * - Paar
     - Bitstring mit Zielbit 0
     - Bitstring mit Zielbit 1
   * - ``(0, 2)``
     - ``000``
     - ``010``
   * - ``(1, 3)``
     - ``001``
     - ``011``
   * - ``(4, 6)``
     - ``100``
     - ``110``
   * - ``(5, 7)``
     - ``101``
     - ``111``

Lokale Matrixmultiplikation
---------------------------

Für jedes Paar werden beide Eingangsamplituden gelesen und gemeinsam
transformiert:

.. math::

   \begin{pmatrix}a'_0\\a'_1\end{pmatrix}
   =
   \begin{pmatrix}U_{00}&U_{01}\\U_{10}&U_{11}\end{pmatrix}
   \begin{pmatrix}a_0\\a_1\end{pmatrix}.

Die Funktion schreibt in einen neu angelegten Ergebnisvektor und verändert den
Eingabevektor nicht.

Die beiden Funktionen
----------------------

:func:`~quantum_circuit_simulator.alt_numpy_einsum.apply_single_qubit_unitary`
   Enthält den eigentlichen Algorithmus. Eingabe und Ausgabe sind flache
   Statevectoren mit :math:`2^n` Elementen.

:func:`~quantum_circuit_simulator.alt_numpy_einsum.apply_single_qubit_gate`
   Ist ein Adapter zum Tensorformat des Simulators. Er formt den Tensor mit
   ``order="F"`` zum Vektor um, ruft die erste Funktion auf und formt das
   Ergebnis wieder zu ``(2,) * num_qubits``.

Validierung
-----------

Die Kernfunktion prüft:

* mindestens ein Qubit;
* einen gültigen Ziel-Qubit-Index;
* einen eindimensionalen Statevector;
* genau :math:`2^n` Amplituden;
* eine Matrix der Form ``(2, 2)``.

Sie prüft nicht numerisch, ob die Matrix tatsächlich unitär ist.
