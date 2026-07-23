# expense-quality-monitor

Progetto per ridurre il controllo manuale settimanale degli export CSV delle note spese, che possono contenere dati mancanti, duplicati, valori non validi, importi anomali e spese soggette a policy.

## Stato attuale

I requisiti sono stati consolidati, il dataset sintetico è stato progettato, il generatore deterministico è stato implementato e il design della soluzione è stato completato. È stato creato lo scaffolding importabile del monolite modulare. Il motore di analisi, la dashboard completa e i test delle regole non sono ancora implementati.

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

## Avvio della shell

```bash
streamlit run app.py
```

La shell presenta soltanto il titolo e lo stato dell'integrazione. Non analizza ancora file CSV.

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
    └── test_package_import.py
```

## Convenzione dei commit

I messaggi di commit dovranno iniziare con uno dei prefissi:

- `human:` per contenuto principalmente scritto o modificato dalla persona;
- `ai-generated:` per contenuto principalmente generato dall'AI;
- `ai-assisted:` per contenuto realizzato dalla persona con assistenza AI.
