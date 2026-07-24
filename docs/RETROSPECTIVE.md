# Retrospettiva

## In quali fasi l'AI ha aiutato di più?

L'AI ha accelerato soprattutto la trasformazione progressiva del brief in artefatti verificabili: requisiti, specifica del dataset, design, implementazione, test e documentazione. È stata utile per generare rapidamente alternative, individuare casi limite e preparare test avversariali. Ha contribuito anche alla costruzione del generatore deterministico, del motore modulare, della dashboard e della CI.

Il beneficio principale non è stato ottenere codice al primo tentativo, ma poter iterare rapidamente tra proposta e verifica. La ground truth row-level e i test automatici hanno fornito un riscontro indipendente sulle proposte generate. L'AI è rimasta uno strumento del processo di sviluppo: non viene usata durante l'analisi dei CSV.

## Quando è stato necessario fermarsi e correggere l'AI?

È stato necessario intervenire già nella definizione delle assunzioni, quando l'AI aveva dichiarato chiuse tutte le ambiguità dopo le risposte del richiedente. Restavano invece decisioni operative indispensabili per rendere i controlli deterministici.

La revisione più sostanziale ha riguardato il primo generatore: distribuiva male gli scenari di policy, applicava la normalizzazione oltre lo scopo previsto e duplicava buona parte del futuro motore. In seguito, test mirati hanno rilevato problemi meno visibili nella gestione dei valori mancanti pandas, dei dtype testuali, dei duplicati logici e di una colonna aggiuntiva in conflitto con la numerazione tecnica. Lo smoke test ha infine evidenziato la telemetria predefinita di Streamlit. I dettagli e le motivazioni delle correzioni sono registrati in `docs/REVIEW_NOTES.md`.

## Cosa sarebbe stato fatto diversamente?

Partirei ancora prima da una tabella unica che colleghi requisito, assunzione, `rule_id`, scenario sintetico e test. Questo avrebbe reso immediatamente visibili le sovrapposizioni tra anomalie statistiche e policy e avrebbe ridotto le revisioni della specifica.

Definirei inoltre fin dall'inizio il confine tra validazione strutturale del generatore e logica applicativa, per evitare la prima versione sovra-ingegnerizzata. Inserirei i test avversariali sui tipi pandas e lo smoke test Streamlit appena disponibili i relativi componenti. Verificherei infine i deliverable del brief con una checklist automatizzabile prima della documentazione conclusiva.

## Qual è stata la parte più difficile?

La difficoltà maggiore è stata gestire l'ambiguità senza trasformare decisioni operative in requisiti inventati. La distinzione tra validazione stretta e normalizzazione, il significato di osservazione statisticamente utilizzabile e le sovrapposizioni tra anomalia, approvazione e non conformità richiedevano precisione semantica prima ancora che tecnica.

Sul piano implementativo, la parte più delicata è stata preservare i valori grezzi rendendo al tempo stesso affidabili parsing e confronti. Valori `NaN`, `StringDtype`, importi con separatori diversi e ID testuali mostrano perché il confronto con il solo dataset dimostrativo non è sufficiente.

## Risultati completati

Sono stati completati generatore sintetico deterministico, dataset e ground truth, motore di controlli, reporting ed export CSV, dashboard Streamlit, test automatici, CI e documentazione. La soluzione opera localmente su dati sintetici e produce risultati confrontabili con la ground truth.

## Limiti

L'analisi riguarda un singolo CSV settimanale. Non sono implementati limite dimensionale del caricamento, conversione valutaria, storico multi-settimana, autenticazione, API, database, integrazione ERP, deployment o AI nel runtime.

## Miglioramenti futuri

Prima di estendere il prodotto, misurerei il processo operativo in un contesto ammesso dalla governance e raccoglierei feedback sulla leggibilità dei risultati. Valuterei un limite configurabile del file, test end-to-end stabili per la dashboard e pinning o lock delle dipendenze. Ogni estensione di dominio richiederebbe nuovi requisiti e test dedicati.
