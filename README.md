# expense-quality-monitor

![Flusso di Expense Quality Monitor](docs/assets/expense-quality-monitor-flow.png)

Strumento locale per automatizzare il controllo settimanale degli export CSV delle note spese. Il problema affrontato è la presenza ricorrente di dati mancanti, valori non validi, duplicati, importi anomali e spese soggette ad approvazione, oggi verificati manualmente prima del riepilogo per il CFO.

## Soluzione

Il progetto implementa un monolite modulare deterministico che:

1. carica e valida lo schema del CSV;
2. conserva i valori originali e crea valori di lavoro normalizzati;
3. applica regole indipendenti di qualità, anomalia e policy;
4. produce segnalazioni ordinate e verificabili;
5. presenta metriche, riepiloghi, filtri e download tramite Streamlit.

Il motore non usa modelli AI nel runtime e non effettua chiamate esterne durante l’analisi.

## Stack e architettura

- Python 3.11 o successivo;
- pandas per caricamento e analisi tabellare;
- Streamlit per la dashboard;
- pytest per test unitari, di integrazione, regressione e interfaccia;
- Ruff per lint e formattazione;
- Bandit per la scansione di sicurezza;
- GitHub Actions per la CI.

L’architettura è un monolite modulare: `pipeline.py` coordina il flusso, mentre caricamento, normalizzazione, regole e reporting restano separati. Questa struttura mantiene semplice l’esecuzione locale e rende ogni controllo verificabile in isolamento.

## Dati e governance

Sono ammessi esclusivamente dati sintetici. Non devono essere caricati dati aziendali, di clienti o di persone reali, né devono essere inviati a strumenti AI.

Il dataset dimostrativo è:

```text
data/synthetic_expenses.csv
```

La relativa ground truth è:

```text
data/expected_anomalies.csv
```

## Controlli implementati

- completezza dei sei campi obbligatori;
- validità di identificativo, data, importo e categoria;
- duplicati per `id_spesa` ripetuto;
- duplicati logici con identificativi diversi e confronto normalizzato;
- anomalie statistiche per categoria oltre tre volte la mediana;
- non valutabilità statistica sotto cinque osservazioni utilizzabili;
- soglie di policy e stato `richiede approvazione`;
- non conformità sopra soglia senza approvatore.

Le regole, le soglie e i messaggi sono centralizzati e deterministici. L’export CSV delle segnalazioni neutralizza valori che potrebbero essere interpretati come formule da un foglio di calcolo.

## Dashboard Streamlit

La dashboard:

- carica un CSV esclusivamente in memoria;
- mostra righe totali, righe con segnalazioni e segnalazioni complessive;
- presenta conteggi per tipo, stato e categoria;
- filtra le segnalazioni per `anomaly_type` e `status`;
- esporta in CSV i risultati filtrati.

Gli errori di caricamento noti vengono mostrati con messaggi comprensibili; gli errori inattesi non espongono dettagli interni o contenuti del file.

## Risultati verificati

Sul dataset dimostrativo:

- 300 righe sintetiche;
- 37 righe con almeno una segnalazione;
- 43 segnalazioni attese;
- corrispondenza esatta con la ground truth;
- 41 test automatici superati.

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## Generazione del dataset

```bash
python3 scripts/generate_dataset.py
```

La generazione usa il seed fisso `20260713`, una settimana sintetica fissa e sovrascrive deterministicamente:

- `data/synthetic_expenses.csv`;
- `data/expected_anomalies.csv`.

## Avvio della dashboard

```bash
streamlit run app.py
```

Per la dimostrazione caricare `data/synthetic_expenses.csv`.

## Test e qualità

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m bandit -r src app.py -c pyproject.toml
python3 -m compileall src tests app.py
python3 -m pip check
```

La workflow `.github/workflows/ci.yml` esegue su push e pull request verso `main` la rigenerazione dei dataset, il controllo delle differenze, i test, Ruff, Bandit e compileall. Non sono previsti CD o deployment.

## Struttura del repository

```text
.
├── .github/workflows/ci.yml
├── .streamlit/config.toml
├── README.md
├── TIME_LOG.md
├── app.py
├── data/
│   ├── expected_anomalies.csv
│   └── synthetic_expenses.csv
├── docs/
│   ├── ASSUNZIONI.md
│   ├── CASE_STUDY.md
│   ├── DEMO.md
│   ├── RETROSPECTIVE.md
│   ├── REVIEW_NOTES.md
│   ├── brief.md
│   ├── dataset.md
│   ├── design.md
│   └── requirements.md
├── pyproject.toml
├── scripts/generate_dataset.py
├── src/expense_quality_monitor/
│   ├── config.py
│   ├── loader.py
│   ├── normalization.py
│   ├── pipeline.py
│   ├── reporting.py
│   └── rules/
└── tests/
    ├── test_app.py
    ├── test_loader.py
    ├── test_package_import.py
    ├── test_pipeline_reporting.py
    ├── test_regression.py
    ├── test_rules.py
    └── test_tool_configuration.py
```

## Limiti e fuori ambito

- analisi limitata a un singolo file settimanale;
- nessuna conversione valutaria;
- nessun dato reale;
- nessuna autenticazione, API, integrazione ERP o database;
- nessuna analisi storica multi-settimana;
- nessun deployment o CD;
- nessun modello AI nel runtime.

## Commit e tracciabilità AI

I messaggi di commit devono iniziare con:

- `human:` per contenuto principalmente scritto o modificato dalla persona;
- `ai-generated:` per contenuto principalmente generato dall’AI;
- `ai-assisted:` per contenuto realizzato dalla persona con assistenza AI.

Assunzioni e correzioni critiche degli output AI sono documentate rispettivamente in `docs/ASSUNZIONI.md` e `docs/REVIEW_NOTES.md`.
