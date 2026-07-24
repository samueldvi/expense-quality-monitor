# Case study — Expense Quality Monitor

## 1. Contesto

L’Ufficio Amministrazione riceve ogni settimana un export CSV delle note spese. Il richiedente ha indicato che il controllo manuale del file e la preparazione del riepilogo per il CFO richiedono circa cinque ore alla settimana.

## 2. Problema

Il formato può contenere campi obbligatori mancanti, date e importi non validi, categorie non ammesse, spese duplicate, importi anomali e superamenti delle soglie di policy. Il controllo manuale rende più difficile applicare le stesse regole in modo ripetibile e ricostruire perché una riga è stata segnalata.

## 3. Obiettivo

Automatizzare il controllo di qualità e delle anomalie di un export settimanale, producendo segnalazioni deterministiche e un riepilogo consultabile tramite una dashboard essenziale.

## 4. Soluzione

La soluzione carica il CSV come testo, verifica lo schema, conserva i valori originali, crea valori di lavoro normalizzati e applica regole indipendenti. Il risultato contiene una riga per ogni segnalazione, ordinata per riga sorgente e regola. Streamlit presenta metriche, riepiloghi, filtri e download CSV.

## 5. Architettura

È stato scelto un monolite modulare in Python:

- `loader.py` gestisce acquisizione e schema;
- `normalization.py` prepara i valori di lavoro;
- `rules/` separa le famiglie di controllo;
- `pipeline.py` coordina il flusso;
- `reporting.py` produce riepiloghi ed export;
- `app.py` contiene soltanto l’interfaccia Streamlit.

La soluzione usa pandas, Streamlit, pytest, Ruff, Bandit e GitHub Actions. Non sono presenti microservizi o componenti distribuiti.

## 6. Controlli implementati

- completezza dei campi obbligatori;
- validità di identificativo, data, importo e categoria;
- duplicati per identificativo;
- duplicati logici con identificativi diversi;
- valutabilità statistica per categoria;
- anomalie strettamente superiori a tre volte la mediana;
- richieste di approvazione sopra soglia;
- non conformità sopra soglia senza approvatore.

Anomalia statistica, richiesta di approvazione e non conformità restano classificazioni distinte.

## 7. Dataset sintetico e ground truth

Il generatore standard-library produce 300 righe riferite alla settimana sintetica dal 13/07/2026 al 17/07/2026, usando il seed `20260713`. Gli scenari intenzionali sono registrati in `data/expected_anomalies.csv` nello stesso momento in cui vengono introdotti.

La ground truth contiene 43 segnalazioni e consente di verificare sia l’assenza di risultati mancanti sia l’assenza di risultati aggiuntivi. Tutti i nomi, codici e contenuti sono sintetici.

## 8. Risultati misurabili

- 300 righe nel dataset dimostrativo;
- 37 righe con almeno una segnalazione;
- 43 segnalazioni prodotte dal motore;
- corrispondenza esatta tra output e ground truth;
- 50 test automatici superati;
- controlli locali Ruff, Bandit e compileall superati.

Il progetto non misura ancora il tempo effettivamente risparmiato nel processo amministrativo e non attribuisce un beneficio economico.

## 9. Sicurezza e governance

- uso esclusivo di dati sintetici;
- elaborazione locale senza chiamate esterne;
- telemetria Streamlit disabilitata;
- nessuna credenziale nel repository;
- neutralizzazione della formula injection nell’export;
- scansione Bandit del codice runtime;
- permessi read-only per i contenuti nella CI;
- tracciabilità dei commit e delle correzioni AI.

## 10. Ruolo dell’AI

L’AI ha assistito analisi, generazione del dataset, implementazione, test, revisione e documentazione. Non viene usata nel runtime. Le sue proposte sono state sottoposte a verifica tramite specifiche, test, ground truth e revisioni critiche documentate.

## 11. Limiti

La soluzione analizza un singolo CSV settimanale. Non include dati reali, conversione valutaria, storico multi-settimana, autenticazione, database, API, integrazione ERP, deployment o modelli AI nel runtime.

## 12. Valore per Amministrazione e CFO

Per l’Ufficio Amministrazione il progetto rende i controlli ripetibili, espliciti e rieseguibili sullo stesso input. Per il CFO offre un riepilogo strutturato e una tabella esportabile delle segnalazioni. Il potenziale impatto sul tempo operativo dovrà essere misurato in un utilizzo futuro; non è stato stimato come risultato di questo esercizio.
