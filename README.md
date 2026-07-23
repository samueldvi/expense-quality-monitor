# expense-quality-monitor

Progetto per ridurre il controllo manuale settimanale degli export CSV delle note spese, che possono contenere dati mancanti, duplicati, valori non validi, importi anomali e spese soggette a policy.

## Stato attuale

I requisiti sono consolidati e il monolite modulare include il generatore del dataset sintetico, il motore deterministico, la dashboard Streamlit e test unitari, di integrazione, regressione e interfaccia. Una CI GitHub Actions verifica generazione, test, lint, formattazione, sicurezza e compilazione. Non è previsto deployment.

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

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
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

## Test e qualità

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m bandit -r src app.py -c pyproject.toml
python3 -m compileall src tests app.py
```

## Avvio della dashboard

```bash
streamlit run app.py
```

Per una dimostrazione può essere caricato `data/synthetic_expenses.csv`. La dashboard mostra metriche complessive, conteggi per tipo e stato, riepilogo per categoria, filtri sulle segnalazioni e download CSV sicuro dei risultati filtrati.

## Struttura attuale

```text
.
├── .gitignore
├── .github
│   └── workflows
│       └── ci.yml
├── .streamlit
│   └── config.toml
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
    ├── test_app.py
    ├── test_loader.py
    ├── test_package_import.py
    ├── test_pipeline_reporting.py
    ├── test_regression.py
    ├── test_rules.py
    └── test_tool_configuration.py
```

## Convenzione dei commit

I messaggi di commit dovranno iniziare con uno dei prefissi:

- `human:` per contenuto principalmente scritto o modificato dalla persona;
- `ai-generated:` per contenuto principalmente generato dall'AI;
- `ai-assisted:` per contenuto realizzato dalla persona con assistenza AI.
