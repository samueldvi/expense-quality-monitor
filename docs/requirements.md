# Requisiti

## Contesto

Ogni settimana l'Ufficio Amministrazione riceve un export CSV con le note spese dei dipendenti. Il formato può contenere dati mancanti, importi anomali, righe duplicate e valori non validi. Il controllo manuale e la preparazione di un riepilogo per il CFO richiedono attualmente circa cinque ore alla settimana.

## Obiettivo

Realizzare uno strumento che riceva un file di note spese, esegua automaticamente controlli di qualità e di anomalia e presenti un riepilogo delle anomalie della settimana in un piccolo cruscotto.

## Stakeholder

- Ufficio Amministrazione: riceve il CSV ed esegue oggi i controlli manuali.
- Impiegato addetto al controllo: utilizzatore operativo del risultato dell'analisi.
- CFO: destinatario del riepilogo.
- Nicola: richiedente che ha fornito i chiarimenti ufficiali.
- Samuel: destinatario dell'esercizio e responsabile della realizzazione.
- Team Vibe Lab: team nel cui contesto operativo è simulato l'intervento.

## Schema CSV confermato

| Colonna | Obbligatoria | Formato o contenuto atteso | Note |
|---|---|---|---|
| `id_spesa` | Sì | Identificativo numerico progressivo | La ripetizione identifica un duplicato. |
| `data_spesa` | Sì | Data nel formato `DD/MM/YYYY` | Il valore può arrivare sporco e deve essere validato. |
| `dipendente` | Sì | Cognome e nome | Campo soggetto al controllo di completezza. |
| `centro_di_costo` | No | Non specificato | Può mancare. |
| `categoria` | Sì | Uno dei valori ammessi | Valori ammessi: Vitto, Trasporto, Alloggio, Materiale, Rappresentanza, Formazione. |
| `descrizione` | No | Testo libero | Spesso vuoto. |
| `importo` | Sì | Importo in EUR con separatore decimale virgola o punto | Deve essere numerico e non negativo. |
| `valuta_originale` | No | Valuta della spesa estera | Presente in caso di spesa in valuta estera. |
| `progetto` | Sì | Codice progetto | Esempio di formato ricevuto: `PRJ-2026-001`. |
| `approvatore` | No | Valore dell'approvatore | Può mancare sulle spese sotto soglia. |

## Requisiti funzionali

### Acquisizione e validità

- Acquisire un file CSV settimanale contenente lo schema confermato.
- Verificare la presenza delle colonne previste.
- Segnalare come incomplete le righe in cui manca uno dei campi obbligatori: `id_spesa`, `data_spesa`, `dipendente`, `categoria`, `importo`, `progetto`.
- Accettare l'assenza dei campi facoltativi: `centro_di_costo`, `descrizione`, `valuta_originale`, `approvatore`, salvo le regole di policy applicabili ad `approvatore`.
- Validare `data_spesa` rispetto al formato `DD/MM/YYYY`, intercettando anche i valori sporchi o non validi.
- Interpretare `importo` in EUR accettando virgola o punto come separatore decimale.
- Segnalare importi non numerici o negativi.
- Verificare che `categoria` appartenga all'insieme: Vitto, Trasporto, Alloggio, Materiale, Rappresentanza, Formazione.

### Unicità

- Segnalare come duplicato ogni `id_spesa` ripetuto.
- Segnalare come duplicato logico ogni coppia o gruppo di righe con `id_spesa` diverso e gli stessi valori di `dipendente`, `data_spesa`, `importo` e `categoria`.

### Anomalia statistica

- Calcolare le anomalie utilizzando esclusivamente i dati della singola settimana.
- Valutare separatamente ogni categoria.
- Segnalare una spesa come anomalia statistica quando il suo importo supera tre volte la mediana degli importi della categoria.
- Se una categoria contiene meno di cinque osservazioni utilizzabili, indicarla come `non valutabile statisticamente` e applicare come fallback la soglia di policy fissa della categoria.

### Policy e conformità

| Categoria | Soglia |
|---|---:|
| Vitto | 80 EUR |
| Trasporto | 200 EUR |
| Alloggio | 250 EUR |
| Materiale | 150 EUR |
| Rappresentanza | 300 EUR |
| Formazione | 500 EUR |

- Segnalare una spesa sopra la soglia della categoria come `richiede approvazione`.
- Non considerare automaticamente non conforme una spesa soltanto perché supera la soglia.
- Segnalare come `non conforme: supera soglia senza approvatore assegnato` una spesa che supera la soglia della categoria e ha il campo `approvatore` vuoto.

### Output

- Distinguere nei risultati:
  - `anomalia statistica`: importo superiore a tre volte la mediana della categoria, quando statisticamente valutabile;
  - `richiede approvazione`: importo superiore alla soglia di policy della categoria;
  - `non conforme`: importo superiore alla soglia con `approvatore` vuoto.
- Produrre un controllo di qualità e delle anomalie.
- Mostrare in un piccolo cruscotto un riepilogo delle anomalie della settimana.
- Utilizzare il dataset sintetico incluso nel repository, che contiene volutamente valori nulli, duplicati, importi anomali e formati errati.

### Interfaccia e localizzazione

- Rendere l'interfaccia disponibile in italiano e inglese.
- Rilevare il locale iniziale tra le lingue supportate e consentire una scelta esplicita
  mantenuta nella sessione.
- Conservare file, sezione, filtri, risultati ed export durante il cambio lingua.
- Mantenere canonici e non tradotti nomi delle colonne CSV, `rule_id` e valori esportati;
  localizzare soltanto la presentazione.

### Profilo dati e Dizionario dati

- Mostrare un profilo per colonna con completezza, valori distinti, tipi osservati e
  attesi, intervalli validi e segnalazioni correlate.
- Mostrare un Dizionario dati derivato dalla configurazione canonica dei dieci campi,
  includendo obbligatorietà, formato, valori ammessi e regole applicabili.
- Calcolare profilo e dizionario senza modificare i DataFrame canonici dell'analisi.

### Governance locale

- Mostrare nome, dimensione e formato della sorgente, timestamp UTC dell'elaborazione,
  conteggi strutturali, colonne aggiuntive e versione applicativa disponibile.
- Calcolare un fingerprint SHA-256 sui byte originali del file.
- Mostrare il catalogo delle 17 regole derivato dalle fonti canoniche, con dimensione di
  qualità, stato prodotto, campi e parametri effettivi.
- Riepilogare numero di regole, segnalazioni e righe coinvolte per le cinque dimensioni
  supportate: completezza, validità, unicità, anomalia statistica e conformità alle policy.
- Consentire l'inserimento facoltativo di data owner, data steward, unità organizzativa,
  periodo e note, conservandoli esclusivamente nella sessione corrente.
- Non includere timestamp o responsabilità nella ground truth o nell'export delle
  segnalazioni.

## Criteri di accettazione

1. Un CSV privo di una colonna prevista viene segnalato indicando la colonna mancante.
2. Una riga priva di almeno un campo obbligatorio viene segnalata come incompleta; l'assenza di un campo facoltativo non produce da sola la stessa segnalazione.
3. Una data non valida o non conforme a `DD/MM/YYYY` viene segnalata.
4. Un importo espresso con virgola o punto decimale viene interpretato; un importo negativo o non numerico viene segnalato.
5. Una categoria fuori dall'insieme ammesso viene segnalata.
6. Due righe con lo stesso `id_spesa` vengono segnalate come duplicate.
7. Due righe con `id_spesa` diverso ma stessi `dipendente`, `data_spesa`, `importo` e `categoria` vengono segnalate come duplicati logici.
8. In una categoria con almeno cinque righe, un importo superiore a tre volte la mediana della categoria viene segnalato come anomalia statistica.
9. Una categoria con meno di cinque osservazioni utilizzabili viene indicata come `non valutabile statisticamente` e le sue spese vengono valutate tramite la soglia di policy fissa.
10. Una spesa sopra la soglia della propria categoria viene segnalata come `richiede approvazione`.
11. Una spesa sopra soglia con `approvatore` valorizzato non viene classificata come non conforme per questa regola.
12. Una spesa sopra soglia con `approvatore` vuoto riceve il messaggio `non conforme: supera soglia senza approvatore assegnato`.
13. Anomalia statistica, richiesta di approvazione e non conformità rimangono classificazioni distinte.
14. L'interfaccia è utilizzabile in italiano e inglese senza alterare i valori canonici
    esportati.
15. Il Profilo dati e il Dizionario dati riportano i dieci campi canonici e derivano dalle
    configurazioni applicative.
16. Il fingerprint mostrato coincide con lo SHA-256 dei byte originali della sorgente.
17. Il catalogo contiene esattamente i 17 `rule_id` configurati e il riepilogo usa soltanto
    le cinque dimensioni supportate.
18. Le responsabilità sono facoltative, persistono tra lingua e sezione nella stessa
    sessione e vengono azzerate quando cambia sorgente.

## Requisiti non funzionali

- Il progetto deve essere sviluppato con un processo strutturato: requisiti, design, implementazione e verifica.
- Il codice deve essere leggibile, organizzato, mantenibile e accompagnato da test automatici eseguibili.
- La soluzione deve includere un controllo di qualità del codice e una scansione di sicurezza di base.
- La dashboard può essere leggera; la perfezione estetica non è un obiettivo della valutazione.
- Le ore impiegate devono essere registrate in modo effettivo, senza stime retrospettive.
- La documentazione deve comunicare in modo trasparente assunzioni, uso dell'AI e correzioni critiche dei suoi output.
- Metadati e responsabilità della Governance non devono essere salvati automaticamente né
  inviati a servizi esterni.

## Vincoli di governance

- Non devono essere usati dati aziendali o di clienti reali: sono ammessi esclusivamente dati sintetici.
- I dati reali di clienti non devono essere inseriti nei prompt.
- I messaggi di commit devono descrivere il contenuto della modifica secondo le convenzioni
  definite in `CONTRIBUTING.md`; l'eventuale assistenza AI resta soggetta a revisione umana
  e non determina il tipo di commit.
- Le assunzioni devono essere dichiarate esplicitamente senza presentarle come requisiti.
- Almeno due casi reali di correzione, rifiuto o modifica critica di output AI devono essere annotati durante il progetto.

## Chiarimenti del richiedente

**Data:** 2026-07-23  
**Canale:** Microsoft Teams  
**Stato:** Risposte ricevute e recepite

### Domande inviate a Nicola

1. Quali colonne contiene normalmente il CSV e quali sono obbligatorie?
2. È presente un identificativo univoco della spesa oppure devo definire una regola per riconoscere i duplicati?
3. Per individuare gli importi anomali posso usare uno storico oppure devo basarmi solo sui dati della singola settimana?
4. Quando una spesa supera una soglia di policy, deve essere solo segnalata come “richiede approvazione” oppure considerata non conforme?

### Risposte ricevute

1. Lo schema comprende dieci colonne: sei obbligatorie (`id_spesa`, `data_spesa`, `dipendente`, `categoria`, `importo`, `progetto`) e quattro facoltative (`centro_di_costo`, `descrizione`, `valuta_originale`, `approvatore`), con formati e valori riportati nello schema confermato.
2. Devono essere controllati sia gli `id_spesa` ripetuti sia i duplicati logici con identificativo diverso e stessi dipendente, data, importo e categoria.
3. Le anomalie devono usare soltanto la singola settimana, essere calcolate per categoria e applicare il limite di tre volte la mediana; sotto cinque righe la categoria non è valutabile statisticamente e si usa la soglia di policy.
4. Il superamento della soglia richiede approvazione ma non è automaticamente non conforme; la non conformità si verifica soltanto se la soglia è superata e `approvatore` è vuoto.

## Ambiguità ancora aperte

I quattro punti sottoposti a Nicola sono stati chiariti integralmente. Restano necessarie assunzioni operative per rendere deterministici e testabili i controlli; sono dichiarate in `docs/ASSUNZIONI.md`.
