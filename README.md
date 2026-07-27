# Expense Quality Monitor

[![CI](https://github.com/samueldvi/expense-quality-monitor/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/samueldvi/expense-quality-monitor/actions/workflows/ci.yml)

[Apri la demo online](https://samueldvi-expense-quality-monitor-app-elpqlb.streamlit.app/)

## TL;DR

Expense Quality Monitor riceve un CSV di spese, applica controlli deterministici e produce segnalazioni motivate, riepiloghi ed export filtrabili. È pensato per amministrazione, finance e controllo di gestione, con risultati consultabili attraverso una dashboard.

## Demo online

La versione dimostrativa è disponibile su [Streamlit Community Cloud](https://samueldvi-expense-quality-monitor-app-elpqlb.streamlit.app/).

Usare esclusivamente dati sintetici o controllati, privi di informazioni aziendali o personali reali.

## Anteprima

<!-- Screenshot della dashboard da aggiungere in docs/assets/dashboard-overview.png -->

## Per chi è pensato

- uffici amministrativi che verificano periodicamente le note spese;
- team finance e controllo di gestione che preparano riepiloghi;
- responsabili delle note spese che devono esaminare eccezioni e policy;
- data quality specialist e consulenti che controllano flussi CSV periodici.

## Problema affrontato

Il controllo manuale dei file di spesa rende difficile individuare con continuità campi mancanti, valori non validi, duplicati, anomalie e superamenti delle soglie di policy. Senza un processo ripetibile, anche il riepilogo delle eccezioni e la motivazione delle segnalazioni risultano meno verificabili.

Il progetto applica le stesse regole a ogni esecuzione e restituisce una vista ordinata delle righe da approfondire. Non sono stati misurati risparmi economici o temporali.

## Cosa offre

- caricamento di CSV con separatore virgola o punto e virgola;
- file di esempio versionato per esplorare il flusso;
- confronto dello schema con le colonne attese;
- controlli di completezza, validità, unicità, statistica e policy;
- ricerca e filtri sulle segnalazioni;
- dashboard con metriche e riepiloghi;
- export CSV della vista corrente.

## Come funziona

![Flusso di Expense Quality Monitor](docs/assets/expense-quality-monitor-flow.png)

1. caricamento del CSV;
2. validazione dello schema;
3. normalizzazione dei valori di lavoro;
4. esecuzione delle regole deterministiche;
5. generazione delle segnalazioni;
6. analisi dei risultati ed export.

## Struttura del CSV

Il file usa queste dieci colonne canoniche:

```text
id_spesa
data_spesa
dipendente
centro_di_costo
categoria
descrizione
importo
valuta_originale
progetto
approvatore
```

Sono supportati i separatori `,` e `;` e la codifica UTF-8 con o senza BOM. Gli spazi esterni e le differenze tra maiuscole e minuscole nelle intestazioni vengono normalizzati prima del confronto con lo schema. Le colonne aggiuntive sono accettate, ma non partecipano alle regole.

Dall’app è possibile scaricare un modello CSV con le colonne già predisposte. Formati, obbligatorietà e criteri di validazione sono descritti nei [requisiti](docs/requirements.md).

## Risultati del file di esempio

Il dataset controllato incluso nel repository produce:

| Misura | Risultato |
|---|---:|
| Righe analizzate | 300 |
| Righe da verificare | 37 |
| Segnalazioni | 43 |
| Regole coinvolte | 17 |

Seed, scenari intenzionali e ground truth sono documentati nella [specifica del dataset](docs/dataset.md).

## Avvio locale

Richiede Python 3.11 o successivo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Per provare il flusso senza preparare un file, selezionare **Prova con l’esempio** nella schermata iniziale.

## Test e qualità

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

La versione corrente dispone di 75 test automatici. GitHub Actions rigenera il dataset, verifica la ground truth ed esegue test, Ruff, Bandit e compilazione dei sorgenti. A parità di input e versione, la pipeline produce risultati deterministici.

## Architettura

Il progetto è un monolite modulare: l’interfaccia coordina componenti separati, mentre regole e reporting restano indipendenti dalla dashboard.

```text
loader → normalizzazione → regole → pipeline → reporting → dashboard
```

Responsabilità, scelte e alternative sono descritte nel [design della soluzione](docs/design.md).

## AI e controllo umano

L’AI è stata usata come supporto durante implementazione, revisione e documentazione, con un processo **human-in-the-loop**. Requisiti, assunzioni e decisioni sono stati verificati dall’autore; ogni modifica è stata riesaminata tramite diff e sottoposta ai controlli disponibili prima dell’accettazione. Nessun modello AI viene eseguito nel runtime dell’applicazione.

Le correzioni degli output AI sono registrate nelle [note di revisione](docs/REVIEW_NOTES.md); la valutazione del processo è raccolta nella [retrospettiva](docs/RETROSPECTIVE.md).

## Limiti attuali

- analisi di un singolo file per volta;
- nessuno storico persistente;
- nessuna autenticazione;
- nessun database;
- nessuna conversione valutaria;
- nessuna integrazione con sistemi aziendali;
- validazione eseguita su un dataset controllato.

## Documentazione

| Documento | Contenuto |
|---|---|
| [Requisiti](docs/requirements.md) | Schema, regole e criteri di accettazione. |
| [Dataset](docs/dataset.md) | Scenari sintetici, seed e ground truth. |
| [Design](docs/design.md) | Architettura, flusso e scelte tecniche. |
| [Case study](docs/CASE_STUDY.md) | Contesto, soluzione e risultati del progetto. |
| [Case sheet](docs/CASE_SHEET.md) | Sintesi, tempi, leva e trasferibilità. |
| [Guida demo](docs/DEMO.md) | Percorso guidato per una dimostrazione di 20 minuti. |
| [Retrospettiva](docs/RETROSPECTIVE.md) | Valutazione dell’uso dell’AI e del processo. |
| [Note di revisione](docs/REVIEW_NOTES.md) | Problemi rilevati e correzioni motivate. |
| [Registro delle ore](TIME_LOG.md) | Sessioni e durata effettiva del lavoro. |

## Licenza

Licenza non ancora definita. Il repository è attualmente privato.
