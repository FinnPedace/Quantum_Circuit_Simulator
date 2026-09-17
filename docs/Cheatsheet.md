# Projekt-Cheatsheet

Kompakte Übersicht über Werkzeuge und Konzepte, die im Laufe des Projekts
verwendet wurden.

## Git und GitHub

### Wichtige Befehle

| Befehl | Zweck |
|---|---|
| `git status` | Geänderte, neue und vorgemerkte Dateien anzeigen |
| `git diff` | Noch nicht vorgemerkte Änderungen anzeigen |
| `git add <datei>` | Änderungen für den nächsten Commit vormerken |
| `git commit -m "Nachricht"` | Vorgemerkte Änderungen committen |
| `git push` | Lokale Commits zum Remote-Repository übertragen |
| `git pull --ff-only` | Remote-Änderungen ohne automatischen Merge-Commit übernehmen |
| `git fetch` | Remote-Stand laden, ohne lokale Branches zu verändern |
| `git switch <branch>` | Branch wechseln |
| `git switch -c <branch>` | Neuen Branch erstellen und dorthin wechseln |
| `git merge <branch>` | Einen Branch in den aktuellen Branch integrieren |
| `git clone <url>` | Repository lokal kopieren |
| `git log --oneline --graph --all` | Kompakten Branch-Graph anzeigen |

### Begriffe

- **Fast-forward merge:** Der Ziel-Branch wird ohne zusätzlichen Merge-Commit
  auf einen neueren Commit verschoben.
- **Fork:** Eigene GitHub-Kopie eines fremden Repositorys.
- **Pull Request:** Vorschlag, Änderungen eines Branches zu prüfen und zu
  integrieren.
- **Git Graph:** Grafische Darstellung von Branches und Commits, beispielsweise
  als VS-Code-Erweiterung.
- **`.gitignore`:** Legt Dateien und Ordner fest, die Git nicht neu
  versionieren soll, etwa Caches oder Build-Ausgaben.

## Python-Entwicklungswerkzeuge

### uv und `pyproject.toml`

[`uv`](https://docs.astral.sh/uv/) verwaltet Python-Versionen,
Abhängigkeiten, virtuelle Umgebungen und Befehlsausführung.

```bash
uv sync                     # Projektumgebung installieren/aktualisieren
uv sync --group dev         # Development-Abhängigkeiten mitinstallieren
uv add <paket>              # Laufzeitabhängigkeit hinzufügen
uv add --dev <paket>        # Development-Abhängigkeit hinzufügen
uv run <befehl>             # Befehl in der Projektumgebung ausführen
```

`pyproject.toml` enthält unter anderem:

- Projektname und Version,
- benötigte Python-Version,
- Laufzeit- und Development-Abhängigkeiten,
- Konfigurationen für Build- und Entwicklungswerkzeuge.

### Pre-Commit

Pre-Commit führt konfigurierte Hooks aus, beispielsweise YAML-Prüfung,
Whitespace-Korrektur oder Black-Formatierung.

Die Hooks werden in `.pre-commit-config.yaml` mit YAML-Syntax eingetragen:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v2.3.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
```

`repo` bezeichnet die Hook-Quelle, `rev` die verwendete Version und `hooks`
die daraus aktivierten Prüfungen. Einrückungen sind in YAML Teil der Syntax.

```bash
uv tool run pre-commit install             # lokalen Git-Hook installieren
uv tool run pre-commit run --all-files     # alle Dateien manuell prüfen
```

Der automatische Lauf vor jedem Commit erfolgt erst nach `pre-commit install`.
In CI kann `pre-commit run --all-files` unabhängig vom lokalen Hook ausgeführt
werden.

### Ruff

Ruff ist ein schneller Linter und Formatter:

```bash
uv tool run ruff check .
uv tool run ruff check --fix .
uv tool run ruff format .
```

### Statische Typprüfung

Werkzeuge wie **mypy** oder **Pyright** prüfen Typannotationen, ohne das
Programm auszuführen. Sie finden beispielsweise falsch verwendete Parameter
oder unvereinbare Rückgabewerte.

### Numba

Numba ist ein Just-in-Time-Compiler für numerischen Python-Code. Mit `@njit`
markierte Funktionen werden beim ersten Aufruf analysiert und in nativen
Maschinencode übersetzt. Dadurch können rechenintensive Schleifen deutlich
schneller laufen als im Python-Interpreter.

```python
from numba import njit

@njit(cache=True)
def add_arrays(left, right):
    result = left.copy()
    for index in range(left.size):
        result[index] += right[index]
    return result
```

Der erste Aufruf enthält die Kompilierungszeit. Laufzeitvergleiche benötigen
deshalb einen ungemessenen Warm-up-Aufruf. Numba eignet sich besonders für
numerische Schleifen mit NumPy-Arrays und einfachen Datentypen, nicht für
beliebigen dynamischen Python-Code.

### pytest

Tests liegen üblicherweise im Verzeichnis `tests/` und beginnen mit `test_`.

```bash
uv run pytest                          # gesamte Testsuite
uv run pytest -q                       # kompakte Ausgabe
uv run pytest tests/test_gate_fusion.py
uv run pytest -k "cnot"                # Tests nach Namen filtern
```

## Sphinx-Dokumentation

Sphinx erzeugt aus RST-Dateien und Python-Docstrings eine verlinkte
HTML-Dokumentation.

Agentic AI kann beim Erstellen und Pflegen der Dokumentation unterstützen,
beispielsweise indem sie Quellcode analysiert, erste Erklärungen formuliert,
Beispiele ergänzt und fehlende API-Beschreibungen findet. Die generierten
Inhalte müssen fachlich geprüft werden. Ein strenger Sphinx-Build stellt danach
sicher, dass Seitenstruktur, Querverweise und Autodoc-Importe funktionieren.

```bash
# Normaler HTML-Build
uv run sphinx-build -b html docs docs/_build/html

# Vollständiger, strenger Build: Cache ignorieren und Warnungen als Fehler
uv run sphinx-build -E -W --keep-going -b html docs docs/_build/html

# Lokalen Webserver starten
uv run python -m http.server 8000 --directory docs/_build/html
```

Danach ist die Dokumentation unter <http://localhost:8000> oder direkt über
`docs/_build/html/index.html` erreichbar.

## GitHub Actions und CI

**Continuous Integration (CI)** führt Prüfungen automatisch auf einem
GitHub-Runner aus, zum Beispiel bei Pushes oder Pull Requests.

```yaml
on:                    # Trigger, z. B. push oder pull_request
jobs:                  # Auszuführende Jobs
  test:
    runs-on: ubuntu-latest
    steps:             # Schritte eines Jobs
      - uses: actions/checkout@v7
      - run: uv run pytest
```

Typische CI-Aufgaben:

- Pre-Commit-Hooks und Formatierung prüfen,
- pytest ausführen,
- Sphinx mit `-W` bauen,
- Logs oder Patches als **Artifacts** bereitstellen.

Ein roter Formatierungs-Check kann bedeuten, dass der Formatter Änderungen
erzeugt hat. Diese müssen lokal übernommen und erneut committed werden.

## Agentic Coding Tools

- Eine **Sandbox** begrenzt Datei-, Prozess- und gegebenenfalls
  Netzwerkzugriffe eines Coding-Agenten.
- Der Agent sollte nur innerhalb des freigegebenen Projektverzeichnisses
  arbeiten.
- Berechtigungen und Modell können je nach Client beispielsweise über
  `/permissions` und `/model` gesteuert werden.
- Docker stellt reproduzierbare, isolierte Entwicklungsumgebungen bereit.
  Docker Desktop kann unter Windows beispielsweise über `winget` installiert
  werden; der genaue Paketname hängt von der verwendeten Distribution ab.

## Qiskit-Grundlagen

```python
from qiskit import QuantumCircuit

circuit = QuantumCircuit(2)
circuit.h(0)             # Hadamard auf q0
circuit.x(1)             # X-Gate auf q1
circuit.cx(0, 1)         # CNOT: Control q0, Target q1
circuit.measure_all()    # alle Qubits am Ende messen
```

### Basisordnung

Qiskit zeigt einen Basiszustand in der Reihenfolge

```text
|q[n-1] ... q1 q0>
```

`q0` steht also ganz rechts und ist das niederwertigste Bit. Für drei Qubits
gehört Statevector-Index `1` zu `|001>` und Index `4` zu `|100>`.

### Aer

`AerSimulator` dient als performanter Referenzsimulator. Im Projekt werden die
eigenen Statevector-Ergebnisse bis auf eine globale Phase mit Aer verglichen.
Zufällige Counts sollten nicht blind eintragsweise verglichen werden, weil
verschiedene Zufallszahlengeneratoren unterschiedliche korrekte Samples liefern
können.

## Statevector und Tensor-Kontraktion

Ein Zustand aus `n` Qubits lässt sich in Bra-Ket-Schreibweise entwickeln als

$$
|\psi\rangle = \sum_{x=0}^{2^n-1} \alpha_x |x\rangle.
$$

Ein Ein-Qubit-Gate besitzt die Darstellung

$$
U = \sum_{o=0}^{1}\sum_{i=0}^{1} U_{oi}|o\rangle\langle i|.
$$

Wirkt `U` beispielsweise auf Qubit `k`, bleiben alle anderen Qubit-Indizes
erhalten. Nur über den Eingangsindex `i` des Ziel-Qubits wird summiert:

$$
\psi'_{q_0,\ldots,o,\ldots,q_{n-1}}
= \sum_{i=0}^{1}
U_{oi}\,\psi_{q_0,\ldots,i,\ldots,q_{n-1}}.
$$

Der gemeinsame Index `i` verschwindet durch die Summation. Genau diese
Summation über gemeinsame Indizes heißt **Tensor-Kontraktion** und wird im
Projekt mit `numpy.einsum` beschrieben.

Im Simulator wird der Vektor als Tensor mit einer Achse pro Qubit dargestellt:

```python
tensor = np.reshape(statevector, (2,) * num_qubits, order="F")
```

`order="F"` ist entscheidend: Tensorachse `i` entspricht dadurch Qiskit-Qubit
`i`. `numpy.einsum` beschreibt anschließend die Summation über die
Gate-Eingangsachsen. Ein System mit `n` Qubits besitzt `2**n` Amplituden. Die
Anwendung eines lokalen Gates benötigt deshalb `O(2**n)` statt der ungefähr
`O(4**n)` Operationen einer allgemeinen dichten `2**n × 2**n`-Matrix.


## Checkliste vor einem Push

```bash
uv tool run pre-commit run --all-files
uv run pytest
uv run sphinx-build -E -W --keep-going -b html docs docs/_build/html
git status
```
