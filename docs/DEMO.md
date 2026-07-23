# Guida demo — 5–7 minuti

## Preparazione

Da eseguire prima della demo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 scripts/generate_dataset.py
```

Il file da caricare è:

```text
data/synthetic_expenses.csv
```

## 1. Introduzione al problema — 30–40 secondi

Mostrare il README e spiegare che l’Ufficio Amministrazione riceve un CSV settimanale potenzialmente sporco. Il controllo manuale deve individuare incompletezze, valori non validi, duplicati, anomalie di importo e superamenti di policy prima del riepilogo per il CFO.

Sottolineare che la demo usa esclusivamente dati sintetici.

## 2. Architettura — 40–50 secondi

Mostrare la struttura `src/expense_quality_monitor/` e spiegare:

- loader e normalizzazione preparano i dati senza sovrascrivere i valori grezzi;
- le regole sono separate per responsabilità;
- la pipeline coordina;
- reporting costruisce riepiloghi ed export;
- `app.py` usa le API pubbliche senza duplicare le regole.

La scelta è un monolite modulare, proporzionato a un singolo flusso locale e a un CSV settimanale contenuto.

## 3. Avvio della dashboard — 20–30 secondi

Con l’ambiente virtuale attivo:

```bash
streamlit run app.py
```

Mostrare il titolo, la descrizione e l’avviso synthetic-only.

## 4. Caricamento del dataset — 30–40 secondi

Caricare:

```text
data/synthetic_expenses.csv
```

Spiegare che il file resta in memoria e viene passato al motore deterministico.

## 5. Metriche principali — 40–50 secondi

Mostrare e spiegare le tre metriche:

- `Righe totali`: 300;
- `Righe con segnalazioni`: 37;
- `Segnalazioni totali`: 43.

Chiarire che una riga può produrre più segnalazioni quando le regole si sovrappongono intenzionalmente.

## 6. Riepiloghi — 40–50 secondi

Mostrare:

- conteggi per tipo di anomalia;
- conteggi per stato;
- riepilogo per categoria.

Spiegare che anomalie statistiche, richieste di approvazione e non conformità sono risultati distinti.

## 7. Filtri — 30–40 secondi

Usare i filtri `Tipo di anomalia` e `Stato`. Mostrare che:

- nessuna selezione visualizza tutte le segnalazioni;
- il numero dei risultati cambia con i filtri;
- l’ordinamento resta per `source_row_number` e `rule_id`.

## 8. Download — 20–30 secondi

Usare `Scarica le segnalazioni filtrate`. Spiegare che il CSV mantiene lo schema stabile e neutralizza i prefissi `=`, `+`, `-` e `@` per ridurre il rischio di formula injection nei fogli di calcolo.

## 9. Test e CI — 50–60 secondi

Nel terminale eseguire:

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m bandit -r src app.py -c pyproject.toml
```

Mostrare `.github/workflows/ci.yml` e spiegare che la CI:

1. rigenera il dataset;
2. verifica che i CSV versionati non cambino;
3. esegue test, lint, format check, sicurezza e compilazione.

La suite locale verificata contiene 41 test, incluso il confronto esatto con la ground truth.

## 10. Conclusione — 30–40 secondi

Ricapitolare:

- controlli deterministici e verificabili;
- 300 righe sintetiche e 43 segnalazioni attese;
- dashboard locale e CSV esportabile;
- nessuna AI nel runtime e nessun dato reale.

Concludere indicando i limiti: singola settimana, nessuna conversione valutaria, storico, autenticazione, database, API, integrazione ERP o deployment. Possibili evoluzioni devono partire da requisiti aggiuntivi e da una misurazione reale del processo operativo.
