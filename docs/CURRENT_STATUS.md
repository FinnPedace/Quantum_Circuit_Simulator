# Aktueller Entwicklungsstand

Diese Datei beschreibt den tatsächlichen Zwischenstand der eigenen
Statevector-Implementierung. Sie ist kein Zielentwurf: Nicht implementierte
Funktionen sind ausdrücklich als offen markiert.

## Überblick

Die öffentliche Funktion `simulate(...)` in `api.py` verwendet aktuell
`StatevectorSimulator` aus `simulator.py`. Der frühere `AerSimulatorWrapper`
existiert weiterhin als Referenzimplementierung, wird jedoch nicht mehr durch
die öffentliche API aufgerufen.

```text
simulate(circuit, config)
        |
        v
StatevectorSimulator.simulate(...)
        |
        +-- Circuit validieren
        +-- |0...0> erzeugen
        +-- Ein-Qubit-Gates per np.einsum anwenden
        +-- Statevector zurückgeben
```

## Bereits implementiert

### Öffentliche Datenstrukturen

```python
SimulationConfig(shots=1024, seed=None)
SimulationResult(statevector=np.ndarray, counts=dict[str, int] | None)
```

Der Statevector wird immer zurückgegeben. Der Standardzustand vor jeder
Simulation ist `|0...0>`.

### Circuit-Validierung

`StatevectorSimulator._validate_circuit(...)` akzeptiert derzeit:

- `barrier` (wird ignoriert),
- Ein-Qubit-Operationen mit einer 2×2-Matrix aus `operation.to_matrix()`,
- `cx` als erlaubte Operation,
- Endmessungen aller Qubits in höchstens einem Classical Register.

Sie lehnt derzeit ab:

- mehrere Classical Registers,
- Teilmessungen,
- Gates nach einer Messung,
- Operationen ohne unterstützte 2×2-Matrix und außer `cx`.

### Ein-Qubit-Gates

Ein-Qubit-Gates werden als 2×2-Matrix auf einen Zustandstensor angewandt.
Der anfängliche flache Statevector wird mit

```python
np.reshape(state, (2,) * num_qubits, order="F")
```

in einen Tensor umgeformt. Das `order="F"` ist wichtig: Tensorachse `i`
entspricht damit Qiskit-Qubit `i`.

Die Anwendung selbst geschieht durch `np.einsum(...)`. Anschließend wird der
Tensor wieder mit `order="F"` in einen flachen Statevector zurückverwandelt.

Die vorhandenen Tests bestätigen den Aer-Abgleich für:

- `X`, `Y`, `Z` und `H`,
- das parametrische Gate `RX(pi / 3)`,
- ein selbst definiertes Ein-Qubit-`UnitaryGate`.

### CNOT

`cx` wird als allgemeine Zwei-Qubit-Tensor-Kontraktion mit `np.einsum`
ausgeführt. Der CNOT-Tensor hat die Achsen

```text
[control_out, target_out, control_in, target_in]
```

und bildet `|c, t>` auf `|c, t XOR c>` ab. Bei jeder CNOT-Anweisung werden
Control und Target mit `circuit.find_bit(...)` bestimmt. Damit funktioniert
auch `cx(0, 2)` auf einem Drei-Qubit-Circuit.

## Noch nicht implementiert

### Measurement Sampling und Counts

Messanweisungen verändern den zurückgegebenen Statevector nicht; das ist
korrekt, weil der Statevector den Zustand **vor** der Endmessung darstellen
soll. Es gibt jedoch noch kein Sampling der Messergebnisse.

Am Ende von `simulate(...)` steht deshalb aktuell:

```python
return SimulationResult(statevector=final_sv, counts=None)
```

Für Circuits mit `measure_all()` muss später aus

```python
probabilities = np.abs(final_sv) ** 2
```

mit `config.shots` und einem durch `config.seed` initialisierten
Zufallszahlengenerator gesampelt werden. Das Ergebnis muss ein
Qiskit-kompatibles Count-Dictionary ergeben, z. B. `{"00": 512, "11": 488}`.

### Gate Fusion

Gate Fusion ist bislang nicht implementiert. Die Simulation verarbeitet jede
Operation einzeln in ihrer Circuit-Reihenfolge. Die spätere Optimierung kann
benachbarte Ein-Qubit-Gates auf demselben Qubit über

```python
fused = U2 @ U1
```

zusammenfassen und vor `cx`, Messung oder Circuit-Ende anwenden.

## Teststatus

`tests/test_aer_simulator.py` verwendet die öffentliche `simulate()`-API und
vergleicht Statevectoren unabhängig mit Qiskit Aer. Damit bleiben die Tests
gleich, obwohl die API inzwischen den eigenen Simulator verwendet.

Derzeitige Einordnung:

| Testgruppe | Erwarteter Stand |
| --- | --- |
| Ein-Qubit-Gates | grün |
| Eigenes `UnitaryGate` | grün |
| Deterministische Counts | rot, bis Sampling implementiert ist |
| Bell-State-Statevector | grün; Count-Prüfung rot, bis Sampling implementiert ist |
| Nicht benachbartes CNOT-Statevector | grün; Count-Prüfung rot, bis Sampling implementiert ist |
| Zufälliger unterstützter Circuit | Statevector korrekt bis auf numerische Rundungsreste; Counts rot |

Bei Statevector-Vergleichen sollte eine kleine numerische Toleranz verwendet
werden, beispielsweise `atol=1e-12`, da Aer und NumPy bei mathematisch
verschwindenden Amplituden Rundungsreste im Bereich von etwa `1e-17` erzeugen
können.

## Nächste Schritte

1. Sampling aus `abs(statevector) ** 2` implementieren.
2. Deterministische und probabilistische Count-Tests ausführen.
3. Toleranz beim Statevector-Test ergänzen.
4. Erst danach Gate Fusion als optionale Optimierung angehen.
