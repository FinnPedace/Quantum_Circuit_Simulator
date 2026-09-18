Installation
============

Voraussetzungen
---------------

Das Projekt benötigt:

* Python 3.13 oder neuer,
* `uv <https://docs.astral.sh/uv/>`_ zur Verwaltung der Umgebung,
* NumPy, Numba, Qiskit, Qiskit Aer und Matplotlib als
  Laufzeitabhängigkeiten.

Projekt installieren
--------------------

Nach dem Klonen werden im Projektverzeichnis die Laufzeitabhängigkeiten
installiert:

.. code-block:: console

   uv sync

Für Tests und Dokumentation wird zusätzlich die Development-Gruppe benötigt:

.. code-block:: console

   uv sync --group dev

Installation prüfen
-------------------

Ein kurzer Importtest zeigt die installierte öffentliche API:

.. code-block:: console

   uv run python -c "import quantum_circuit_simulator as qcs; print(qcs.__all__)"

Die vollständige Testsuite wird so gestartet:

.. code-block:: console

   uv run pytest
