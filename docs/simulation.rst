Simulationsablauf
=================

Dieses Kapitel beschreibt den Ablauf in
:meth:`quantum_circuit_simulator.simulator.StatevectorSimulator.simulate`.

1. Validierung
--------------

Vor jeder numerischen Berechnung läuft ``_validate_circuit`` über
``circuit.data``. Barrieren werden akzeptiert, ``measure`` markiert den Beginn
der Messphase, ``cx`` wird explizit erlaubt und andere Operationen müssen eine
2×2-Matrix liefern.

Nach der ersten Messung sind nur weitere Messungen oder Barrieren zulässig.
Sobald überhaupt gemessen wird, muss die Menge der gemessenen Qubits alle
Circuit-Qubits enthalten.

2. Startzustand
---------------

Für :math:`n` Qubits wird ein komplexer Vektor mit :math:`2^n` Einträgen
angelegt:

.. math::

   |\psi_0\rangle = |0\ldots0\rangle
                   = (1, 0, \ldots, 0)^T.

Anschließend wird er mit ``order="F"`` in einen Tensor mit einer Achse pro
Qubit umgeformt.

3. Ein-Qubit-Kontraktion
------------------------

Eine Ein-Qubit-Matrix :math:`U` wird entlang der Zielachse kontrahiert. Für
Ziel-Qubit :math:`i` berechnet ``np.einsum`` konzeptionell

.. math::

   \psi'_{q_0,\ldots,o_i,\ldots,q_{n-1}}
   = \sum_{q_i=0}^{1}
     U_{o_i,q_i}\,
     \psi_{q_0,\ldots,q_i,\ldots,q_{n-1}}.

Die Implementierung reserviert ``num_qubits`` als neuen symbolischen
Ausgangsindex und ersetzt damit in den Output-Achsen die Zielachse. Durch Gate
Fusion wird diese Kontraktion nicht zwingend für jedes einzelne Gate
ausgeführt; siehe :doc:`gate_fusion`.

4. CNOT-Kontraktion
-------------------

Der globale ``CNOT_TENSOR`` besitzt die Form ``(2, 2, 2, 2)`` und die
Achsenreihenfolge

.. code-block:: text

   [control_output, target_output, control_input, target_input]

Für jeden binären Eingang :math:`(c,t)` wird genau der Eintrag

.. math::

   C[c,\,t\oplus c,\,c,\,t] = 1

gesetzt. Damit gilt die gewünschte Abbildung

.. math::

   |c,t\rangle \mapsto |c,t\oplus c\rangle.

Vor einer CNOT-Kontraktion werden alle ausstehenden Ein-Qubit-Matrizen
angewendet. Danach kontrahiert ein zweites ``np.einsum`` gleichzeitig die
Control- und Target-Eingangsachse.

5. Barrieren und Messanweisungen
--------------------------------

``barrier`` und ``measure`` verändern den Zustandstensor in der Gate-Schleife
nicht. Beide bilden aber eine Fusionsgrenze: Zuvor gepufferte Matrizen werden
angewendet. Die physikalische Messung wird nicht als Zustandskollaps simuliert,
weil das Ergebnisobjekt den Statevector vor der Endmessung zurückgeben soll.

6. Abschließender Flush
-----------------------

Ein Circuit kann direkt nach einem Ein-Qubit-Gate enden. Deshalb wird der
Fusion-Puffer nach der Schleife noch einmal geleert. Ohne diesen Schritt würden
die letzten Gates nicht in den Endzustand eingehen.

7. Statevector
--------------

Der Tensor wird mit derselben Fortran-Ordnung zurück in einen Vektor
umgeformt. Index :math:`k` entspricht dem Qiskit-Basisbitstring von :math:`k`
mit führenden Nullen.

8. Measurement Sampling
------------------------

Besitzt der Circuit Classical Bits, berechnet der Simulator zunächst

.. math::

   p_k = |\alpha_k|^2.

``numpy.random.Generator.choice`` zieht anschließend ``shots`` Indizes mit
diesen Wahrscheinlichkeiten. Jeder gezogene Index wird als Binärstring der
Länge ``num_qubits`` formatiert und im Count-Dictionary gezählt.

Komplexität
-----------

Der Zustand benötigt :math:`O(2^n)` Speicher. Auch die Anwendung eines
Ein-Qubit-Gates oder CNOTs berührt grundsätzlich :math:`O(2^n)` Amplituden.
Gate Fusion reduziert die Zahl vollständiger Tensor-Kontraktionen, ändert aber
nicht die exponentielle Statevector-Größe.
