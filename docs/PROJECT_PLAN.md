# Bauplan: Quantum Circuit Simulator

Dieser Plan beschreibt die gemeinsame Umsetzung von Problem 2.3. Er trennt die
Arbeit so, dass beide Personen möglichst wenig dieselben Dateien gleichzeitig
ändern und jede Änderung über Tests überprüft werden kann.

## Ziel und Rahmen

Die Bibliothek nimmt einen Qiskit-`QuantumCircuit` entgegen und simuliert ihn
zunächst über einen Aer-Wrapper (Referenzimplementierung), später mit einem
eigenen Statevector-Simulator. Unterstützt werden in Version 1:

- beliebige Ein-Qubit-Unitaries, deren `operation.to_matrix()` eine 2×2-Matrix
  liefert (einschließlich `UnitaryGate`),
- `cx` / CNOT,
- keine Messung oder ausschließlich `circuit.measure_all()` am Circuit-Ende,
- `barrier` als ignorierte Operation.

Nicht unterstützte Gates, Zwischenmessungen, Teilmessungen, Resets, Noise,
klassisch konditionierte Anweisungen und mehrere Classical Registers führen zu
`NotImplementedError`.

Der Statevector nutzt die Qiskit-Basisordnung
`|q[n-1] ... q[1] q[0]>`. Beim Übergang zum Tensor ist deshalb zwingend
`reshape((2,) * n, order="F")` zu verwenden: Tensorachse `i` ist Qubit `i`.

## Feste öffentliche Schnittstelle

Die Schnittstelle wird vor der Implementierung einmal gemeinsam festgelegt und
danach nur bewusst geändert:

```python
@dataclass(frozen=True)
class SimulationConfig:
    shots: int = 1024
    seed: int | None = None


@dataclass(frozen=True)
class SimulationResult:
    statevector: np.ndarray
    counts: dict[str, int] | None


def simulate(
    circuit: QuantumCircuit,
    config: SimulationConfig | None = None,
) -> SimulationResult: ...
```

Regeln:

- `statevector` ist immer der exakte Zustand **vor** den Endmessungen.
- Bei einem Circuit ohne Messungen ist `counts` gleich `None`.
- Bei `measure_all()` enthält `counts` Qiskit-kompatible Bitstrings, zum
  Beispiel `{"00": 508, "11": 492}`.
- `shots` muss mindestens 1 sein.
- Ein gesetzter `seed` macht das Sampling der eigenen Simulation und den
  Aer-Wrapper reproduzierbar.

Die einfache öffentliche API delegiert intern an ein Simulator-Objekt:

```text
simulate(circuit, config)
        |
        +-- AerSimulatorWrapper.simulate(...)      # Phase Mock
        +-- StatevectorSimulator.simulate(...)     # Phase Eigenbau
```

## Zielstruktur

```text
src/quantum_circuit_simulator/
├── __init__.py                    # öffentliche Exports
├── api.py                         # öffentliche simulate()-Funktion
├── config.py                      # SimulationConfig
├── result.py                      # SimulationResult
├── simulator.py                   # gemeinsames Protocol / abstrakte API
├── aer_simulator.py               # Aer-Referenzimplementierung
└── statevector_simulator.py       # eigene Simulation

tests/
├── conftest.py                    # gemeinsame Fixtures und Hilfsfunktionen
├── test_api.py
├── test_aer_simulator.py
└── test_statevector_simulator.py

docs/
└── PROJECT_PLAN.md
```

## Aufgabenverteilung

### Person A: Infrastruktur, API und Aer-Referenz

Verantwortung:

1. `SimulationConfig`, `SimulationResult` und öffentliche Exports erstellen.
2. `Simulator`-Schnittstelle und `api.simulate()` erstellen.
3. `qiskit-aer` als Dependency ergänzen.
4. `AerSimulatorWrapper` implementieren.
   - Counts: ursprünglichen Circuit mit `shots` und `seed_simulator` ausführen.
   - Statevector: Circuit kopieren, Endmessungen entfernen,
     `save_statevector()` hinzufügen und Aer mit `method="statevector"`
     ausführen.
5. Nutzungsbeispiel und unterstützte/nicht unterstützte Features in der README
   dokumentieren.

Eigene Dateien: `config.py`, `result.py`, `simulator.py`, `api.py`,
`aer_simulator.py`, `__init__.py`, `pyproject.toml`, `README.md`.

### Person B: Tests und eigener Simulator

Verantwortung:

1. Teststrategie, Fixtures und Statevector-Vergleichshilfe erstellen.
2. Validierung der erlaubten Circuit-Struktur implementieren.
3. Ein-Qubit-Gates als Tensor-Kontraktion mit `numpy.einsum` implementieren.
4. CNOT als allgemeine Tensor-Kontraktion mit `numpy.einsum` implementieren.
5. Counts durch Sampling aus `abs(statevector) ** 2` erzeugen.
6. Gate-Fusion nur strukturell vorbereiten: interne Operationsliste oder klar
   abgetrennte Ausführungsfunktionen; noch keine Optimierung implementieren.

Eigene Dateien: `tests/`, `statevector_simulator.py`.

### Gemeinsame Entscheidungen und Reviews

Diese Punkte macht ihr zusammen, bevor der jeweilige Pull Request gemergt wird:

- finale Semantik von `measure_all()` und Count-Bitstrings;
- Qiskit-Quibitindex aus `circuit.find_bit(qubit).index`;
- Reihenfolge der Matrixmultiplikation bei Gate Fusion: nach `U1`, dann `U2`
  gilt `fused = U2 @ U1`;
- Lesbarkeit der `einsum`-Indexnotation und Abgleich mit dem Aufgabenblatt;
- Code Review und Testlauf.

Falls eine Person früher fertig wird, übernimmt sie nicht sofort die Dateien der
anderen Person, sondern reviewt den offenen Pull Request oder ergänzt Tests und
Dokumentation. Das vermeidet Merge-Konflikte und verbessert die Qualität.

## Meilensteine und Reihenfolge

| Meilenstein | Ergebnis | Verantwortlich | Abnahmekriterium |
| --- | --- | --- | --- |
| M0: Vertrag | API und Einschränkungen dokumentiert | gemeinsam | Dieser Plan ist abgestimmt |
| M1: Mock | Aer-Wrapper hinter der öffentlichen API | A | Aer-Tests grün |
| M2: Tests | Test-Suite gegen Aer | B | mindestens Gates, Bell, CNOT und Random Circuit |
| M3: Kern | Eigener Ein-Qubit-Statevector-Simulator | B | Statevector gegen Aer korrekt |
| M4: CNOT | CNOT, auch nicht benachbart | B | alle CNOT-Tests korrekt |
| M5: Messung | Sampling und Count-Format | B, Review A | deterministische und statistische Tests grün |
| M6: Abschluss | Dokumentation, Linting, Review | gemeinsam | `pytest` und Pre-commit grün |

M1 und M2 können parallel beginnen. M3 sollte erst auf dem abgestimmten
Resultat-/Config-Vertrag aufbauen. M4 und M5 können nach M3 teilweise parallel
besprochen werden, sollten aber nicht gleichzeitig dieselbe Simulator-Datei
bearbeiten.

## Testplan

### Statevector-Tests

Verglichen wird immer mit Aer **vor** Endmessungen. Der Vergleich muss globale
Phase ignorieren, weil sie physikalisch nicht beobachtbar ist.

- Startzustand `|0...0>`;
- `X`, `Y`, `Z`, `H` und mindestens ein parametrisches Gate, etwa `RX(theta)`;
- mehrere aufeinanderfolgende Ein-Qubit-Gates;
- Bell-State: `H(0)` gefolgt von `CX(0, 1)`;
- CNOT mit benachbarten Qubits;
- CNOT mit nicht benachbarten Qubits, etwa Control 0, Target 2;
- zufällig erzeugter Circuit mit festem Generator-Seed;
- `UnitaryGate` mit eigener zufälliger 2×2-unitärer Matrix;
- nicht unterstützte Operationen und ungültige Messstruktur.

### Mess-Tests

- Deterministische Circuits: `X` und Bell-State liefern exakt erwartete
  Counts.
- Probabilistische Circuits: bei ausreichend vielen Shots liegt zum Beispiel
  die Häufigkeit von `H|0>` nahe bei 0.5, mit sinnvoller Toleranz.
- Circuits ohne Messung liefern `counts is None`.
- Ein gleicher Seed reproduziert die eigene Sampling-Ausgabe.

Aer-Wrapper-Tests dürfen Aer direkt und exakt prüfen. Für den eigenen Simulator
sollten zufällige Shot-Counts nicht blind exakt mit einem Aer-Lauf verglichen
werden: Unterschiedliche Zufallszahlengeneratoren können trotz gleichem Seed
andere, aber korrekte Stichproben liefern.

## Git-Ablauf

`main` bleibt jederzeit lauffähig. Niemand arbeitet direkt auf `main`.

1. Vor einer Aufgabe aktualisieren:

   ```powershell
   git switch main
   git pull --ff-only
   git switch -c feat/aer-wrapper
   ```

2. Ein Branch enthält genau ein abgegrenztes Arbeitspaket. Empfohlene Namen:

   ```text
   feat/public-api
   feat/aer-wrapper
   test/reference-suite
   feat/single-qubit-einsum
   feat/cnot-einsum
   feat/measurement-sampling
   docs/readme
   ```

3. Klein und thematisch committen:

   ```powershell
   git add src/quantum_circuit_simulator/aer_simulator.py tests/test_aer_simulator.py
   git commit -m "feat: add Aer simulator wrapper"
   git push -u origin feat/aer-wrapper
   ```

4. Pull Request gegen `main` öffnen. Die andere Person reviewt mindestens:
   - passt die Änderung zum Schnittstellenvertrag?
   - sind passende Tests enthalten?
   - sind `uv run pytest` und `pre-commit run --all-files` erfolgreich?

5. Erst nach Review mergen. Danach aktualisieren beide ihren lokalen
   `main`-Branch, bevor sie einen neuen Branch starten.

Wenn ihr einmal gleichzeitig dieselbe Datei ändern müsst, legt vorher fest, wer
den Grundaufbau erstellt. Die andere Person arbeitet dann in einer separaten
Testdatei oder kommentiert im Pull Request. Keine ungelösten Merge-Konflikte
blind übernehmen: Konflikt gemeinsam lesen und mit Tests absichern.

## Definition of Done

Das Projekt ist fertig, wenn:

- die öffentliche API dokumentiert und stabil ist;
- der Aer-Wrapper beide Resultatarten korrekt liefert;
- der eigene Simulator nur erlaubte Circuits akzeptiert;
- Single-Qubit-Gates und CNOT per Tensor-/`einsum`-Ansatz funktionieren;
- Statevectoren mit Aer bis auf globale Phase übereinstimmen;
- Count-Tests für deterministische und probabilistische Fälle bestehen;
- mindestens ein zufällig generierter Circuit getestet ist;
- `uv run pytest` und `pre-commit run --all-files` erfolgreich durchlaufen;
- README die Installation, Nutzung sowie die bewussten Einschränkungen nennt.
