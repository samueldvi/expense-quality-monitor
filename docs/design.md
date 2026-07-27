# Design della soluzione

## 1. Contesto e obiettivo

Questo documento descrive l'architettura implementata per caricare un CSV settimanale di note spese, applicare controlli deterministici e presentare segnalazioni verificabili tramite una dashboard. I requisiti e i criteri di accettazione sono definiti in `docs/requirements.md`.

## 2. Vincoli

- Sono ammessi esclusivamente dati sintetici; dati aziendali, di clienti o di persone reali non devono essere usati.
- L'elaborazione avviene localmente.
- Durante l'analisi non vengono effettuate chiamate esterne.
- A parità di input e versione dell'applicazione, l'output deve essere riproducibile.
- Ogni segnalazione deve derivare da una regola esplicita, verificabile e sottoponibile a test.
- La soluzione deve restare semplice, leggibile e mantenibile, in proporzione a un esercizio di cinque giorni e a un dataset settimanale di dimensioni contenute.

## 3. Architettura scelta

La soluzione è un monolite modulare in Python. Questa scelta è adeguata perché il progetto realizza un solo flusso applicativo e tratta un dataset settimanale contenuto. Non esistono esigenze di scalare o distribuire separatamente i componenti; i microservizi introdurrebbero comunicazione tra processi, deployment e gestione operativa non giustificati.

I moduli interni hanno responsabilità e interfacce chiare. Potranno essere separati in futuro soltanto se emergerà una necessità concreta.

Il flusso applicativo è:

1. caricamento del CSV;
2. verifica dello schema;
3. conservazione dei valori grezzi;
4. parsing e normalizzazione in colonne di lavoro;
5. applicazione delle regole;
6. produzione della tabella delle segnalazioni;
7. calcolo del riepilogo;
8. costruzione di Profilo dati, Dizionario dati e viste di Governance;
9. localizzazione e presentazione tramite Streamlit;
10. esportazione CSV delle segnalazioni canoniche.

### Stack

- Python come linguaggio applicativo;
- pandas per caricamento, normalizzazione e analisi tabellare;
- Streamlit per il cruscotto;
- pytest per i test automatici;
- ruff per lint e controllo della formattazione;
- bandit per il controllo di sicurezza del codice Python;
- GitHub Actions per una CI minima.

La CI non include CD; il deployment dimostrativo è gestito separatamente su Streamlit Community Cloud.

### Uso dell'AI

L'AI viene usata nel processo di sviluppo e di revisione, non nel runtime dell'applicazione. Le regole sono già formalizzate e devono produrre risultati deterministici. Un modello generativo nel runtime aggiungerebbe variabilità, costi, complessità e rischi di privacy, rendendo inoltre più difficili test e audit.

## 4. Struttura applicativa

La struttura applicativa è:

```text
expense-quality-monitor/
├── app.py
├── pyproject.toml
├── src/
│   └── expense_quality_monitor/
│       ├── __init__.py
│       ├── config.py
│       ├── governance.py
│       ├── i18n.py
│       ├── loader.py
│       ├── normalization.py
│       ├── profiling.py
│       ├── rules/
│       │   ├── __init__.py
│       │   ├── completeness.py
│       │   ├── uniqueness.py
│       │   ├── validity.py
│       │   ├── statistical.py
│       │   └── policy.py
│       ├── pipeline.py
│       ├── reporting.py
│       └── ui_theme.py
└── tests/
```

Responsabilità dei componenti:

- `app.py`: interfaccia Streamlit e gestione delle azioni dell'utente, senza logica di analisi.
- `pyproject.toml`: metadati del progetto, dipendenze e configurazione degli strumenti.
- `config.py`: schema atteso, categorie, soglie di policy e costanti condivise, definite in un unico punto.
- `loader.py`: lettura UTF-8 con o senza BOM, rilevamento dei separatori `,` e `;`, normalizzazione delle intestazioni, confronto con lo schema canonico e gestione degli errori di acquisizione.
- `normalization.py`: creazione delle colonne di lavoro parsed o normalizzate senza alterare i valori originali.
- `rules/completeness.py`: controlli sui campi obbligatori.
- `rules/uniqueness.py`: duplicati per identificativo e duplicati logici.
- `rules/validity.py`: validità di identificativo, data, importo e categoria.
- `rules/statistical.py`: valutabilità delle categorie e anomalie rispetto alla mediana.
- `rules/policy.py`: soglie, richieste di approvazione e non conformità.
- `pipeline.py`: ordinamento ed esecuzione coordinata delle fasi, senza duplicare le singole regole.
- `reporting.py`: riepiloghi, ordinamento delle segnalazioni ed esportazione CSV.
- `profiling.py`: metriche strutturali, profilo per colonna e Dizionario dati canonico,
  senza rendering.
- `governance.py`: metadati immutabili dell'elaborazione, SHA-256, catalogo tecnico delle
  regole e riepilogo per dimensione, senza dipendenze da Streamlit o traduzioni.
- `i18n.py`: cataloghi italiano e inglese, rilevamento del locale e funzioni di
  localizzazione della presentazione.
- `ui_theme.py`: ruoli, colori e icone semantiche, senza logica di analisi.
- `tests/`: test unitari, di integrazione e di regressione.

`app.py` coordina la navigazione, i widget e lo stato della sessione. Le copie localizzate
dei DataFrame sono create esclusivamente per la presentazione: `AnalysisResult`, ground
truth ed export mantengono valori e colonne canonici.

## 5. Modello dei dati

Il CSV viene caricato inizialmente come testo per preservare esattamente i valori originali, compresi spazi, separatori decimali e valori malformati. Le conversioni non sovrascrivono le colonne sorgente.

Lo schema canonico deriva da `EXPECTED_COLUMNS`. Prima del confronto, il loader rimuove il BOM e gli spazi esterni dai nomi delle colonne e usa `casefold` per ricondurre le intestazioni riconosciute ai nomi canonici. Non applica alias semantici. Le colonne aggiuntive sono ammesse e non partecipano alle regole; eventuali nomi duplicati dopo la normalizzazione interrompono il caricamento.

Il modello interno aggiunge:

- `source_row_number`, che identifica la posizione della riga dati dopo l'intestazione, partendo da 1;
- colonne di lavoro parsed o normalizzate per data, importo, identificativo, dipendente e categoria, create soltanto quando richieste dai controlli.

La validazione della categoria resta stretta sui sei valori esatti confermati. La normalizzazione di spazi e maiuscole/minuscole viene usata per i duplicati logici, non per rendere valido un valore non conforme.

La tabella delle segnalazioni contiene almeno:

| Colonna | Contenuto |
|---|---|
| `source_row_number` | Numero della riga sorgente |
| `id_spesa` | Identificativo originale, se presente |
| `rule_id` | Identificativo stabile della regola |
| `anomaly_type` | Famiglia della segnalazione |
| `field` | Campo interessato |
| `status` | Esito deterministico |
| `message` | Messaggio comprensibile |
| `original_value` | Valore grezzo che ha prodotto la segnalazione |

Una riga sorgente può produrre più segnalazioni quando le sovrapposizioni sono previste dai requisiti.

## 6. Ordine dei controlli

I controlli vengono eseguiti nel seguente ordine:

1. schema;
2. completezza;
3. validità;
4. unicità;
5. valutabilità statistica;
6. anomalie statistiche;
7. policy.

Le fasi successive usano soltanto valori idonei al controllo specifico. Un valore mancante produce la segnalazione di completezza pertinente e non viene segnalato anche come formato non valido. Analogamente, importi mancanti, negativi o non numerici e categorie mancanti o non ammesse non contribuiscono al calcolo della mediana.

Una categoria è statisticamente valutabile soltanto se contiene almeno cinque osservazioni utilizzabili. Un'osservazione è utilizzabile quando la categoria è presente, coincide esattamente con uno dei sei valori validi e l'importo è presente, numerico e non negativo. Se le osservazioni utilizzabili sono meno di cinque, la categoria è `non valutabile statisticamente` e alle relative spese utilizzabili viene applicata soltanto la policy fissa.

## 7. Regole

Il dettaglio vincolante delle regole, comprese soglie e condizioni, è in `docs/requirements.md`. I moduli in `rules/` separano completezza, unicità, validità, statistica e policy; la pipeline ne coordina l'esecuzione senza ridefinirne la logica.

Il confronto dei duplicati logici esclude le righe in cui dipendente, data, importo o categoria sono mancanti o non interpretabili. In particolare, la data deve essere valida, l'importo deve essere numerico e non negativo e la categoria deve coincidere esattamente con un valore ammesso. Queste righe conservano le proprie segnalazioni di completezza o validità, ma non generano falsi duplicati logici.

Anomalia statistica, richiesta di approvazione e non conformità restano classificazioni distinte, anche quando più regole producono segnalazioni sulla stessa riga.

## 8. Gestione degli errori

Gli errori vengono tradotti in messaggi comprensibili e non mostrano stack trace all'utente della dashboard.

La pipeline distingue tre esiti:

- un errore bloccante di caricamento impedisce l'avvio dei controlli sulle righe;
- una segnalazione di riga identifica un problema relativo a una specifica `source_row_number` senza interrompere l'analisi delle altre righe;
- lo stato di categoria `non valutabile statisticamente` indica che le osservazioni utilizzabili sono meno di cinque e non costituisce un errore di caricamento.

| Caso | Comportamento |
|---|---|
| File non leggibile come CSV | Interrompe l'analisi e mostra `Il contenuto non può essere letto come CSV.` |
| File vuoto | Interrompe l'analisi e mostra `Il file è vuoto.` |
| Intestazione mancante o incompatibile | Interrompe l'analisi e mostra le colonne mancanti e quelle trovate |
| Colonne previste mancanti | Interrompe l'analisi ed elenca i nomi mancanti in ordine canonico |
| Colonne aggiuntive | Le ammette e indica che non sono utilizzate nelle regole |
| Colonne duplicate dopo la normalizzazione | Interrompe l'analisi e mostra `Alcune colonne hanno lo stesso nome dopo la normalizzazione.` |
| Nessuna riga utilizzabile | Conserva le segnalazioni di qualità producibili e indica che non esistono righe idonee ai controlli statistici e di policy |

Gli errori tecnici completi possono essere registrati localmente per lo sviluppo, senza includere contenuti sensibili del CSV nell'interfaccia.

## 9. Dashboard e stato di sessione

La dashboard Streamlit comprende:

- caricamento del CSV;
- navigazione stabile tra Panoramica, Segnalazioni, Profilo dati, Governance, Dati ed
  Esporta;
- interfaccia in italiano e inglese con scelta persistente nella sessione;
- metriche, conteggi per tipo e stato e riepilogo per categoria;
- tabella ricercabile e filtrabile delle anomalie;
- profilo per colonna e Dizionario dati dei dieci campi canonici;
- metadati dell'elaborazione, fingerprint SHA-256, catalogo delle 17 regole e riepilogo
  delle cinque dimensioni di qualità;
- responsabilità facoltative conservate soltanto nello stato della sessione;
- download CSV delle segnalazioni.

Il cambio di lingua o sezione conserva sorgente, risultati, filtri, timestamp e
responsabilità. Il cambio della sorgente crea nuovi metadati e azzera le responsabilità
facoltative. La logica di analisi resta nei moduli applicativi e non nell'interfaccia.

## 10. Strategia di test

La strategia comprende:

- unit test per ciascuna famiglia di regole;
- test della pipeline completa e dell'ordine dei controlli;
- test dei casi limite e degli errori di caricamento;
- confronto tra output del motore e `data/expected_anomalies.csv`;
- test di regressione su `data/synthetic_expenses.csv`;
- test separati per le sovrapposizioni intenzionali tra valutabilità statistica, anomalie statistiche, policy e non conformità.

I test verificano sia le segnalazioni attese sia l'assenza di segnalazioni aggiuntive.

## 11. Sicurezza e governance

- Si usano esclusivamente dati sintetici.
- Il repository e l'applicazione non contengono credenziali.
- L'analisi non effettua chiamate esterne.
- Il loader verifica lo schema e la presenza delle colonne richieste.
- Il contenuto del CSV viene trattato come dato e non viene mai eseguito.
- Un limite configurabile alla dimensione del caricamento resta un miglioramento futuro.
- L'esportazione neutralizza valori testuali che potrebbero essere interpretati come formule dai fogli di calcolo.
- La CI rigenera e confronta i dataset, quindi esegue pytest, Ruff, Bandit, compileall e
  `pip check`.
- Il timestamp UTC descrive l'elaborazione corrente, resta separato da `AnalysisResult` e
  non entra nella ground truth o nell'export.
- Il fingerprint SHA-256 è calcolato sui byte originali del file, non su una
  serializzazione del DataFrame.
- Le responsabilità facoltative non sono persistite e non costituiscono assegnazioni
  aziendali.
- I commit descrivono il contenuto della modifica secondo le convenzioni definite in
  `CONTRIBUTING.md`; l'assistenza AI è documentata come parte del processo di revisione e
  non come categoria del commit.
- L'AI assiste sviluppo e revisione, ma non riceve i dati analizzati e non opera nel runtime.

## 12. Alternative considerate

| Scelta | Alternativa non scelta | Motivazione |
|---|---|---|
| pandas | DuckDB | Il dataset settimanale è piccolo e il flusso richiede trasformazioni tabellari dirette; DuckDB aggiungerebbe un motore SQL senza un beneficio proporzionato. |
| Streamlit | Plotly Dash | Streamlit consente di realizzare più rapidamente il cruscotto essenziale; Dash richiederebbe più struttura e callback per lo stesso risultato. |
| Monolite modulare | Microservizi | Un solo flusso, un solo sviluppatore e nessuna esigenza di scalabilità indipendente non giustificano infrastruttura e comunicazione distribuita. |
| Regole deterministiche | LLM nel runtime | Le regole sono formalizzate; un LLM introdurrebbe variabilità, costi, rischi di privacy e maggiore difficoltà di test e audit. |

## 13. Fuori ambito

- autenticazione;
- database;
- API;
- integrazione con ERP;
- analisi storica multi-settimana;
- conversione valutaria;
- CD;
- microservizi;
- modelli AI nel runtime.

## 14. Limiti tecnici correnti

- Non esistono persistenza, autenticazione o lineage operativo persistente.
- Timestamp e responsabilità appartengono esclusivamente alla sessione corrente.
- La Governance rende visibili informazioni locali e deterministiche, ma non costituisce
  una piattaforma aziendale completa di data governance.
- `app.py` supera 1.400 righe e resta un monolite UI di dimensione significativa. La
  separazione futura dei renderer è una possibile manutenzione, non parte di questo audit.
- L'analisi riguarda un solo file settimanale per volta e non mantiene uno storico.
