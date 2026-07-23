# expense-quality-monitor

Progetto per ridurre il controllo manuale settimanale degli export CSV delle note spese, che possono contenere dati mancanti, duplicati, valori non validi, importi anomali e spese soggette a policy.

## Stato attuale

I requisiti sono stati consolidati, il dataset sintetico è stato progettato, il generatore deterministico è stato implementato e il design della soluzione è stato completato. Il monolite modulare include ora il motore deterministico e i relativi test unitari, di integrazione e di regressione. La dashboard completa non è ancora implementata.

## Dati

Il progetto deve utilizzare esclusivamente dati sintetici. Non sono ammessi dati aziendali o di clienti reali, inclusi i prompt inviati agli strumenti AI.

## Generazione dei dataset

```bash
python3 scripts/generate_dataset.py
```

Il comando produce:

- `data/synthetic_expenses.csv`;
- `data/expected_anomalies.csv`.

La generazione crea 300 righe usando il seed fisso `20260713` e una settimana sintetica fissa. Il secondo file contiene la ground truth delle anomalie introdotte intenzionalmente. A parità di versione dello script, gli output sono riproducibili.

## Ambiente di sviluppo

```bash
python3 -m pip install -e ".[dev]"
```

## Analisi del dataset sintetico

```python
from expense_quality_monitor.pipeline import analyze_expenses

result = analyze_expenses("data/synthetic_expenses.csv")
print(result.summary)
print(result.findings)
```

Il motore applica:

- controlli di completezza sui campi obbligatori;
- validità di identificativo, data, importo e categoria;
- duplicati per identificativo e duplicati logici normalizzati;
- valutabilità statistica e anomalie oltre tre volte la mediana;
- soglie di policy, richieste di approvazione e non conformità.

## Test

```bash
.venv/bin/python -m pytest -q
```

## Avvio della shell Streamlit

```bash
streamlit run app.py
```

La shell presenta soltanto il titolo e lo stato dell'integrazione. La dashboard completa non è ancora implementata.

## Struttura attuale

```text
.
├── .gitignore
├── README.md
├── TIME_LOG.md
├── app.py
├── data
│   ├── expected_anomalies.csv
│   └── synthetic_expenses.csv
├── docs
│   ├── ASSUNZIONI.md
│   ├── REVIEW_NOTES.md
│   ├── brief.md
│   ├── dataset.md
│   ├── design.md
│   └── requirements.md
├── pyproject.toml
├── scripts
│   └── generate_dataset.py
├── src
│   └── expense_quality_monitor
│       ├── __init__.py
│       ├── config.py
│       ├── loader.py
│       ├── normalization.py
│       ├── pipeline.py
│       ├── reporting.py
│       └── rules
│           ├── __init__.py
│           ├── completeness.py
│           ├── policy.py
│           ├── statistical.py
│           ├── uniqueness.py
│           └── validity.py
└── tests
    ├── __init__.py
    ├── test_loader.py
    ├── test_package_import.py
    ├── test_pipeline_reporting.py
    ├── test_regression.py
    └── test_rules.py
```

## Convenzione dei commit

I messaggi di commit dovranno iniziare con uno dei prefissi:

- `human:` per contenuto principalmente scritto o modificato dalla persona;
- `ai-generated:` per contenuto principalmente generato dall'AI;
- `ai-assisted:` per contenuto realizzato dalla persona con assistenza AI.
