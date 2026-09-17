Benchmarks
==========

Ziel
----

``benchmarks/benchmark_simulators.py`` misst den vollständigen
Simulationsaufruf für fünf Varianten:

* Qiskit ``AerSimulator`` mit einem einmalig konstruierten Statevector-Backend;
* NumPy-``einsum`` ohne Gate Fusion;
* NumPy-``einsum`` mit Gate Fusion;
* Numba ohne Gate Fusion;
* Numba mit Gate Fusion.

Der erzeugte Circuit enthält pro Qubit jeweils ``rx``, ``ry`` und ``rz`` als
zusammenhängende Fusionsgruppe sowie ein CNOT pro Layer.

Backendobjekte und die Aer-``save_statevector``-Instruktion werden vor der
Messung einmalig vorbereitet. Gemessen wird bei allen Varianten nur der
vollständige Simulationsaufruf mit bereits vorhandenem Circuit und Backend.

Benchmark starten
-----------------

Aus dem Projektverzeichnis:

.. code-block:: console

   uv run python benchmarks/benchmark_simulators.py

Parameter können über die Kommandozeile verändert werden:

.. code-block:: console

   uv run python benchmarks/benchmark_simulators.py \
       --qubits 16 \
       --layers 10 \
       --repeats 9 \
       --warmups 2

``--qubits``
   Anzahl der Qubits. Der Statevector besitzt :math:`2^n` Amplituden.

``--layers``
   Anzahl der Gate-Layer des deterministischen Benchmark-Circuits.

``--repeats``
   Zahl der gemessenen vollständigen Simulationsläufe.

``--warmups``
   Zahl der ungemessenen Aufwärmläufe pro Variante. Mindestens ein Warm-up ist
   erforderlich.

Korrektheitsprüfung
-------------------

Vor jeder Zeitmessung wird jede Variante aufgewärmt und ihr Statevector bis
auf eine globale Phase mit Aer verglichen. Bei einer Abweichung bricht der
Benchmark mit einem Fehler ab. Damit werden keine Laufzeiten inkorrekter
Implementierungen miteinander verglichen.

Numba-Warm-up
-------------

Numba kompiliert einen Kernel beim ersten Aufruf für die konkrete Kombination
aus Datentypen und Speicherlayout. Diese JIT-Kompilierung gehört nicht zur
stationären Gate-Laufzeit und findet deshalb während des ungemessenen Warm-ups
statt. Ein separater Cold-Start-Benchmark müsste die Kompilierungszeit bewusst
einschließen.

Ausgabe interpretieren
----------------------

Die Tabelle enthält:

``Median [ms]``
   Median aller gemessenen vollständigen Simulationsaufrufe. Dieser Wert ist
   robuster gegen einzelne Ausreißer als das Minimum.

``Best [ms]``
   Schnellster beobachteter Lauf.

``Speedup vs Aer``
   Aer-Median geteilt durch den Median der jeweiligen Variante. Werte größer
   als 1 bedeuten, dass die Variante in diesem Lauf schneller war als Aer.

``Speedup vs einsum/no fusion``
   Vergleich mit dem Eigenbau-Ausgangspunkt ohne Gate Fusion.

Benchmarkregeln
---------------

Performancewerte hängen stark von CPU, Betriebssystem, NumPy-/Numba-Version,
Threading und Circuit-Struktur ab. Für belastbare Aussagen sollten daher:

* mehrere Qubitzahlen getestet werden;
* dieselben Parameter und Softwareversionen verwendet werden;
* Hintergrundlast reduziert werden;
* mehrere Wiederholungen betrachtet werden;
* kleine Circuits nicht auf große Statevectoren verallgemeinert werden.

Bei kleinen Zuständen können Python-Wrapper und Funktionsaufrufe den Numba-
Vorteil überdecken. Gate Fusion reduziert außerdem die Zahl der Kernelaufrufe,
sodass isolierte Gate-Speed-ups nicht automatisch dem End-to-End-Speed-up
entsprechen.
