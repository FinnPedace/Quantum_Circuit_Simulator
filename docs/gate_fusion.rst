Gate Fusion
===========

Motivation
----------

Mehrere aufeinanderfolgende Ein-Qubit-Gates auf demselben Qubit können vor der
Anwendung als kleine 2×2-Matrizen multipliziert werden. Für

.. math::

   U_1 \rightarrow U_2 \rightarrow U_3

gilt

.. math::

   U_3(U_2(U_1|\psi\rangle)) = (U_3U_2U_1)|\psi\rangle.

Statt drei Kontraktionen des vollständigen Zustandstensors genügt damit eine
Kontraktion mit der fusionierten Matrix.

Fusion-Puffer
-------------

Der Simulator verwaltet ein Dictionary

.. code-block:: python

   fused_gates: dict[int, np.ndarray] = {}

Der Schlüssel ist der Qubit-Index, der Wert die bisher fusionierte 2×2-Matrix.
Ein neues Gate wird nicht sofort auf den Zustand angewendet. Stattdessen gilt:

.. code-block:: python

   fused_gates[target] = (
       matrix
       if previous_matrix is None
       else matrix @ previous_matrix
   )

Die Links-Multiplikation ist wesentlich. Nach ``H``, ``Rx`` und ``Rz`` muss
die gespeicherte Matrix ``Rz @ Rx @ H`` lauten.

Gates auf verschiedenen Qubits
------------------------------

Innerhalb eines Abschnitts speichert das Dictionary eine Matrix pro Qubit.
Ein-Qubit-Operationen auf **verschiedenen** Qubits können in beliebiger
Reihenfolge auf den Zustand angewendet werden, weil sie auf unterschiedlichen
Tensorfaktoren wirken und miteinander kommutieren.

Fusionsgrenzen
--------------

Der Puffer wird geleert:

* vor jedem ``cx``;
* bei einer ``barrier``;
* bei einer ``measure``-Anweisung;
* nach dem Ende der Gate-Schleife.

CNOT muss eine Grenze bilden, weil Gates vor und nach einer verschränkenden
Operation im Allgemeinen nicht zusammengezogen werden dürfen. Barrieren und
Messungen bilden bewusst strukturelle Grenzen.

Beim Flush durchläuft ``_flush_fused_gates`` alle gespeicherten Einträge,
wendet jede Matrix über ``_apply_single_qubit_gate`` an und leert danach das
Dictionary mit ``clear()``.

Beispiel
--------

Für den Circuit

.. code-block:: python

   circuit.h(0)
   circuit.x(1)
   circuit.rz(0.3, 0)
   circuit.s(1)
   circuit.cx(0, 1)
   circuit.ry(0.5, 0)

entwickelt sich der Puffer so:

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Instruktion
     - Puffer danach
     - Zustand
   * - ``H(0)``
     - ``{0: H}``
     - unverändert
   * - ``X(1)``
     - ``{0: H, 1: X}``
     - unverändert
   * - ``Rz(0)``
     - ``{0: Rz @ H, 1: X}``
     - unverändert
   * - ``S(1)``
     - ``{0: Rz @ H, 1: S @ X}``
     - unverändert
   * - ``CX(0,1)``
     - leer
     - zwei fusionierte Matrizen, dann CNOT angewendet
   * - ``Ry(0)``
     - ``{0: Ry}``
     - seit CNOT unverändert
   * - Circuit-Ende
     - leer
     - ``Ry`` angewendet

Abgrenzung zur alternativen Implementierung
--------------------------------------------

Gate Fusion entscheidet, **welche Matrix** angewendet wird. Das gewählte
Backend entscheidet, **wie diese Matrix** auf den Zustand wirkt. ``einsum``
verwendet eine NumPy-Tensorkontraktion; ``numba`` verwendet die kompilierten
Blockschleifen aus :doc:`alternative_einsum`. Beide Backends können unabhängig
von der Fusion ein- oder ausgeschaltet verglichen werden.
