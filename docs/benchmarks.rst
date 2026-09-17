Benchmarks
==========

Ziel
----

``benchmarks/benchmark_simulators.py`` misst den vollständigen
Simulationsaufruf für fünf Varianten:

* Qiskit ``AerSimulator`` mit einem einmalig konstruierten Statevector-Backend,
  deaktivierter Aer-Gate-Fusion und genau einem CPU-Thread;
* NumPy-``einsum`` ohne Gate Fusion;
* NumPy-``einsum`` mit Gate Fusion;
* Numba ohne Gate Fusion;
* Numba mit Gate Fusion.

Für jede Qubitzahl wird ein reproduzierbarer Zufallscircuit mit exakt 100
Gates erzeugt. Mit einer Wahrscheinlichkeit von 80 % wird eines der
Ein-Qubit-Gates ``h``, ``x``, ``sx``, ``rx``, ``ry`` oder ``rz`` auf ein
zufälliges Qubit angewendet. Die übrigen 20 % sind CNOTs mit verschiedenen,
zufällig gewählten Control- und Target-Qubits. Der feste Seed 42 macht die
Circuits und damit den Vergleich reproduzierbar.

Backendobjekte und die Aer-``save_statevector``-Instruktion werden vor der
Messung einmalig vorbereitet. Gemessen wird bei allen Varianten nur der
vollständige Simulationsaufruf mit bereits vorhandenem Circuit und Backend.
Die Aer-Optionen ``fusion_enable=False`` und ``max_parallel_threads=1``
verhindern dabei interne Gate Fusion und parallele Statevector-Updates.

Skalierungsplot
---------------

Der für die README erzeugte Plot vergleicht standardmäßig 4, 8, 12, 16 und
20 Qubits auf einer logarithmischen Zeitachse:

.. image:: images/benchmark_simulators.png
   :alt: Laufzeitvergleich von Aer, einsum und Numba mit und ohne Gate Fusion
   :align: center

Er kann zusammen mit den zugrunde liegenden CSV-Daten neu erzeugt werden:

.. code-block:: console

   uv run python benchmarks/plot_benchmarks.py

Standardmäßig entstehen ``docs/images/benchmark_simulators.png`` und
``benchmarks/results/benchmark_simulators.csv``.

Benchmark starten
-----------------

Aus dem Projektverzeichnis:

.. code-block:: console

   uv run python benchmarks/benchmark_simulators.py

Parameter können über die Kommandozeile verändert werden:

.. code-block:: console

   uv run python benchmarks/benchmark_simulators.py \
       --qubits 20 \
       --gates 100 \
       --seed 42 \
       --repeats 5 \
       --warmups 2

``--qubits``
   Anzahl der Qubits. Der Statevector besitzt :math:`2^n` Amplituden.

``--gates``
   Exakte Anzahl der zufällig erzeugten Gates im Circuit.

``--seed``
   Seed des Zufallszahlengenerators. Derselbe Seed erzeugt für dieselbe
   Qubitzahl und Gate-Anzahl denselben Circuit.

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
