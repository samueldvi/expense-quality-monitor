# Retrospettiva

## Cosa ha funzionato

Il processo requisiti → assunzioni → specifica del dataset → design → implementazione → test ha ridotto il rischio di adattare i requisiti al codice. La ground truth row-level ha reso verificabile il risultato completo: il test di regressione controlla che non esistano segnalazioni mancanti o aggiuntive.

La separazione tra loader, normalizzazione, regole, pipeline, reporting e dashboard ha mantenuto il motore indipendente da Streamlit. I controlli automatici hanno dato riscontri rapidi durante le revisioni, mentre il generatore deterministico ha permesso di rigenerare i dati senza alterare gli output versionati.

## Cosa è stato più difficile

La parte più impegnativa è stata trasformare chiarimenti funzionali in regole operative non ambigue. Le sovrapposizioni tra anomalie statistiche, soglie di policy e assenza dell’approvatore richiedevano quantità coerenti e confronti stretti. Anche la distinzione tra normalizzazione per i duplicati logici e validazione stretta della categoria ha richiesto una revisione esplicita.

Sul piano tecnico, i casi limite di pandas — valori mancanti parsed e dtype testuali — non emergevano da una lettura superficiale del codice. Lo smoke test della dashboard ha inoltre evidenziato la telemetria predefinita di Streamlit, incompatibile con il vincolo di non effettuare chiamate esterne.

## Decisioni architetturali principali

È stato scelto un monolite modulare perché il progetto ha un unico flusso, un dataset settimanale contenuto e nessuna necessità di scalabilità indipendente. pandas è adeguato alle trasformazioni tabellari richieste; Streamlit consente una dashboard essenziale senza introdurre un frontend separato.

Le configurazioni confermate, il catalogo delle regole e lo schema delle segnalazioni sono centralizzati. I valori grezzi restano separati dai valori parsed o normalizzati. `AnalysisResult` raccoglie dati sorgente, segnalazioni e riepilogo senza introdurre metadata variabili.

## Perché non c’è AI nel runtime

Le regole sono formalizzate e devono essere deterministiche, testabili e auditabili. Un modello generativo nel runtime introdurrebbe variabilità, costi, dipendenze esterne e rischi di privacy senza migliorare controlli già espressi in modo preciso. L’AI è stata usata nel processo di sviluppo, non nell’analisi dei CSV.

## Valore della ground truth

La ground truth è stata registrata insieme agli scenari intenzionali del dataset. Ha permesso di:

- verificare ogni `rule_id`, stato e messaggio atteso;
- controllare le sovrapposizioni previste;
- rilevare segnalazioni mancanti;
- impedire segnalazioni aggiuntive;
- separare l’atteso dalla logica del motore sottoposto a test.

## Problemi reali trovati durante le revisioni

- **REV-001:** l’AI aveva dichiarato chiuse tutte le ambiguità; sono state esplicitate sei assunzioni operative ancora necessarie.
- **REV-002:** il primo generatore distribuiva male gli scenari policy, normalizzava eccessivamente le categorie e duplicava il futuro motore; la specifica è stata corretta e il generatore semplificato.
- **REV-003:** la gestione di `NaN` parsed e `StringDtype` era incompleta; sono stati uniformati i controlli dei valori mancanti e la neutralizzazione dell’export.
- **REV-004:** i duplicati logici richiedevano erroneamente ID numerici e Ruff escludeva troppo codice; sono stati separati presenza e validità degli ID e limitata l’esclusione al formatter.
- **REV-005:** una colonna extra chiamata `source_row_number` causava un errore tecnico; il loader ora preserva il valore con un nome non ambiguo.
- **REV-006:** Streamlit raccoglieva statistiche d’uso per impostazione predefinita; la telemetria è stata disabilitata.

Questi casi mostrano che test, smoke test e confronto con le specifiche sono stati necessari per correggere proposte AI plausibili ma non conformi.

## Funzionalità completate

- generatore sintetico deterministico;
- dataset e ground truth versionati;
- motore completo di qualità, anomalia e policy;
- reporting ed export CSV sicuro;
- dashboard Streamlit con filtri e download;
- test unitari, integrazione, regressione e interfaccia;
- CI minima e controlli locali di qualità e sicurezza;
- documentazione di requisiti, assunzioni, design e revisioni.

## Cosa migliorerei con più tempo

Prima di ampliare il prodotto, misurerei l’uso reale con soli dati ammessi e raccoglierei feedback sulla leggibilità delle segnalazioni e dei riepiloghi. Aggiungerei test end-to-end del caricamento nella dashboard solo se l’API di test di Streamlit lo rendesse stabile, senza mock complessi. Valuterei inoltre un limite di dimensione del file configurabile e verificato esplicitamente al confine di caricamento.

## Evoluzioni possibili

Con requisiti e governance aggiuntivi si potrebbero valutare:

- confronto storico tra settimane;
- integrazione controllata con un sistema sorgente;
- gestione di tassi di cambio;
- autenticazione e autorizzazioni;
- persistenza dei risultati;
- metadata operativi separati per la lineage.

Queste evoluzioni non sono implementate e restano fuori ambito.

## Elementi volutamente esclusi

Non sono stati introdotti microservizi, database, API, autenticazione, ERP, deployment, CD o modelli AI nel runtime. L’esclusione mantiene la soluzione proporzionata all’esercizio e impedisce di presentare come completate capacità non richieste o non verificate.
