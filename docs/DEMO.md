# Guida demo — 20 minuti

## Preparazione

Prima della demo, dalla root del repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 scripts/generate_dataset.py
```

Il file dimostrativo da caricare è `data/synthetic_expenses.csv`.

## 0:00–1:30 — Contesto e problema

- Presentare la richiesta fittizia dell'Ufficio Amministrazione: controllare un CSV settimanale delle note spese e preparare un riepilogo strutturato per il CFO.
- Mostrare le famiglie di problemi: incompletezze, valori non validi, duplicati, anomalie di importo e policy.
- Evidenziare il vincolo non negoziabile: uso esclusivo di dati sintetici.
- Chiarire che le circa cinque ore di controllo manuale sono un dato del brief e che il progetto non ha misurato benefici economici o temporali.

## 1:30–3:30 — Requisiti e assunzioni

- Mostrare `docs/requirements.md`: schema, campi obbligatori, categorie, anomalie statistiche e soglie di policy.
- Riassumere i chiarimenti ricevuti dal richiedente su schema, duplicati, storico e classificazione sopra soglia.
- Mostrare `docs/ASSUNZIONI.md`, distinguendo i requisiti confermati dalle decisioni operative.
- Spiegare perché valori mancanti, confronti stretti, normalizzazione e confronto grezzo degli ID devono essere regole verificabili.

## 3:30–5:30 — Architettura

- Mostrare l'immagine iniziale del README.
- Presentare il monolite modulare e il flusso:
  - `loader.py`: acquisizione e verifica dello schema;
  - `normalization.py`: valori di lavoro senza alterare i valori sorgente;
  - `rules/`: controlli indipendenti;
  - `pipeline.py`: coordinamento deterministico;
  - `reporting.py`: riepiloghi ed export;
  - `app.py`: dashboard Streamlit.
- Ribadire che non sono presenti AI nel runtime, API, database, autenticazione o deployment.

## 5:30–7:30 — Dataset e ground truth

- Eseguire o mostrare il comando:

```bash
python3 scripts/generate_dataset.py
```

- Spiegare seed fisso, settimana sintetica fissa e rigenerazione deterministica.
- Mostrare `data/synthetic_expenses.csv`: 300 righe esclusivamente sintetiche.
- Mostrare `data/expected_anomalies.csv`: 43 segnalazioni attese su 37 righe distinte.
- Chiarire che la ground truth è generata insieme agli scenari intenzionali e che il test di regressione la confronta con il motore senza ricostruire l'atteso tramite le sue funzioni.

## 7:30–12:30 — Dimostrazione della dashboard

Avviare:

```bash
streamlit run app.py
```

Poi:

1. mostrare l'avviso sull'uso esclusivo di dati sintetici;
2. caricare `data/synthetic_expenses.csv`;
3. verificare le metriche: 300 righe, 37 righe con segnalazioni e 43 segnalazioni;
4. mostrare i riepiloghi per tipo, stato e categoria;
5. applicare i filtri per tipo di anomalia e stato;
6. mostrare la tabella ordinata per riga sorgente e regola;
7. scaricare l'export CSV filtrato;
8. spiegare che l'export neutralizza i valori testuali che iniziano con `=`, `+`, `-` o `@` per ridurre il rischio di formula injection nei fogli di calcolo.

## 12:30–14:30 — Test, CI e sicurezza

Eseguire:

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m bandit -r src app.py -c pyproject.toml
```

- Mostrare i 42 test automatici, incluso il confronto esatto con la ground truth.
- Mostrare `.github/workflows/ci.yml`: rigenerazione dei dataset, verifica delle differenze, pytest, Ruff, Bandit e compileall.
- Precisare che Bandit analizza il codice runtime in `src` e `app.py`.
- Ricordare che la telemetria Streamlit è disabilitata, il repository non contiene credenziali e l'analisi non effettua chiamate esterne.

## 14:30–17:00 — Revisione critica dell'AI

Mostrare `docs/REVIEW_NOTES.md` e sintetizzare:

- generatore iniziale non conforme e sovra-ingegnerizzato;
- gestione incompleta di `NaN` e `StringDtype`;
- semantica iniziale errata dei duplicati logici;
- esclusione Ruff inizialmente troppo ampia;
- telemetria Streamlit rilevata tramite smoke test.

Spiegare che specifiche, test avversariali, ground truth e smoke test hanno permesso di rifiutare o correggere output plausibili ma non conformi.

## 17:00–18:30 — Case sheet e leva

- Mostrare `docs/CASE_SHEET.md`.
- Presentare la durata netta effettiva: 11h 05m.
- Presentare la stima motivata senza AI: 18 ore.
- Mostrare il calcolo: `18,0 / 11,0833 = 1,62×`.
- Chiarire che la stima senza AI è una valutazione motivata, non una misurazione.
- Indicare trasferibilità alta del pattern per controlli deterministici su file tabellari, ridefinendo le regole di dominio e senza affermare un riuso già avvenuto.

## 18:30–20:00 — Retrospettiva, limiti e conclusione

- Riassumere cosa ha funzionato: processo guidato dalle specifiche, separazione modulare e verifiche automatiche.
- Evidenziare cosa è stato corretto: scenari del dataset, casi limite pandas, duplicati, configurazione degli strumenti e documentazione.
- Presentare i limiti: singola settimana, nessuna conversione valutaria, storico, autenticazione, API, database, ERP, deployment o AI nel runtime.
- Indicare come miglioramenti futuri un limite configurabile del caricamento, test end-to-end stabili e pinning delle dipendenze, senza presentarli come implementati.
- Concludere con i risultati verificati: 300 righe sintetiche, 37 righe coinvolte, 43 segnalazioni e corrispondenza esatta con la ground truth.
