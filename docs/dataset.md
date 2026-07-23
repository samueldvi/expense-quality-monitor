# Progettazione del dataset sintetico

## 1. Scopo

Il dataset simula un export settimanale di note spese ed è destinato a verificare:

- completezza;
- unicità;
- validità;
- anomalie statistiche;
- controlli di policy;
- casi non valutabili statisticamente.

Tutti i dati saranno sintetici. Non verranno utilizzati dati aziendali, di clienti o di persone reali.

## 2. File previsti

La fase successiva produrrà due file:

- `data/synthetic_expenses.csv`: export sintetico settimanale delle note spese;
- `data/expected_anomalies.csv`: ground truth di ogni segnalazione introdotta intenzionalmente.

Questi file sono soltanto specificati in questa fase e non vengono ancora generati.

## 3. Schema del CSV principale

`data/synthetic_expenses.csv` conterrà esattamente le seguenti colonne, nello stesso ordine, senza colonne tecniche aggiuntive.

| Ordine | Colonna | Obbligatoria | Tipo logico | Formato previsto | Esempio sintetico | Principali casi non validi da testare |
|---:|---|---|---|---|---|---|
| 1 | `id_spesa` | Sì | Intero identificativo | Numero progressivo | `100001` | nullo; valore non numerico; identificativo ripetuto |
| 2 | `data_spesa` | Sì | Data | `DD/MM/YYYY` | `13/07/2026` | nullo; giorno impossibile; mese impossibile; formato diverso da quello previsto |
| 3 | `dipendente` | Sì | Testo | Cognome e nome fittizi | `Riva Elena` | nullo; vuoto; soli spazi |
| 4 | `centro_di_costo` | No | Testo | Codice sintetico o vuoto | `CDC-014` | nessun caso di validità specifico; il valore vuoto è ammesso |
| 5 | `categoria` | Sì | Valore categorico | Uno dei sei valori ammessi | `Trasporto` | nullo; valore fuori dall'insieme ammesso |
| 6 | `descrizione` | No | Testo libero | Testo sintetico o vuoto | `Treno per riunione` | nessun caso di validità specifico; il valore vuoto è ammesso |
| 7 | `importo` | Sì | Numero decimale in EUR | Separatore decimale `,` oppure `.` | `47,50` | nullo; valore negativo; valore non numerico |
| 8 | `valuta_originale` | No | Testo informativo | Codice valuta sintetico o vuoto | `USD` | nessuna validazione o conversione prevista; il valore vuoto è ammesso |
| 9 | `progetto` | Sì | Testo | Codice progetto sintetico, senza imporre una regex | `PRJ-2026-001` | nullo; vuoto; soli spazi |
| 10 | `approvatore` | No | Testo | Nome fittizio o vuoto | `Serra Luca` | nullo, vuoto o soli spazi su una spesa sopra soglia |

I valori nulli, vuoti o composti soltanto da spazi nei campi obbligatori saranno considerati mancanti. Date, importi, categorie e nomi saranno normalizzati prima del controllo dei duplicati logici.

## 4. Dimensione e periodo

- Il CSV principale conterrà esattamente 300 righe di dati, oltre all'intestazione.
- Tutte le date valide apparterranno alla settimana lavorativa sintetica dal 13/07/2026 al 17/07/2026.
- La distribuzione tra giorni, categorie, dipendenti e progetti sarà realistica ma non necessariamente uniforme.
- Almeno l'80% delle righe non conterrà errori intenzionali.
- La generazione userà il seed fisso `20260713`.
- La categoria `Formazione` conterrà esattamente 4 righe complessive.

## 5. Categorie ammesse

I soli valori validi di `categoria` saranno:

- Vitto;
- Trasporto;
- Alloggio;
- Materiale;
- Rappresentanza;
- Formazione.

Valori diversi saranno presenti soltanto nei due scenari intenzionali di categoria non ammessa e saranno registrati nella ground truth.

## 6. Caratteristiche delle righe valide

Le righe valide avranno:

- date comprese tra il 13/07/2026 e il 17/07/2026;
- identificativi sintetici progressivi;
- nomi completamente fittizi;
- codici progetto sintetici, come `PRJ-2026-001`, senza assumere un formato regex obbligatorio;
- importi realistici rispetto alla categoria;
- rappresentazioni dell'importo sia con virgola sia con punto come separatore decimale;
- campi facoltativi talvolta vuoti;
- `approvatore` presente sulle spese sopra soglia che devono risultare approvate e facoltativo sulle spese sotto soglia;
- `valuta_originale` valorizzata, quando prevista, soltanto a scopo informativo;
- nessuna conversione valutaria.

## 7. Matrice esatta degli scenari intenzionali

Le quantità indicate contano le righe del CSV principale coinvolte. Le coppie sono composte da due righe ciascuna.

| Area | Scenario | Quantità esatta | Finalità di test |
|---|---|---:|---|
| Completezza | `id_spesa` mancante | 1 riga | Rilevare un identificativo nullo |
| Completezza | `data_spesa` mancante | 1 riga | Rilevare una data vuota |
| Completezza | `dipendente` mancante | 1 riga | Rilevare un nome composto soltanto da spazi |
| Completezza | `categoria` mancante | 1 riga | Rilevare una categoria nulla |
| Completezza | `importo` mancante | 1 riga | Rilevare un importo vuoto |
| Completezza | `progetto` mancante | 1 riga | Rilevare un progetto composto soltanto da spazi |
| Unicità | `id_spesa` ripetuto | 3 coppie, 6 righe | Rilevare entrambi i membri di ogni coppia con lo stesso identificativo |
| Unicità | Duplicato logico con `id_spesa` diverso | 3 coppie, 6 righe | Confrontare dipendente, data, importo e categoria dopo normalizzazione |
| Validità | `id_spesa` non numerico | 1 riga | Verificare che l'identificativo obbligatorio sia numerico |
| Validità | Data non valida | 3 righe | Coprire giorno impossibile, mese impossibile e formato non conforme |
| Validità | Importo negativo | 2 righe | Rifiutare importi minori di zero |
| Validità | Importo non numerico | 2 righe | Rifiutare valori che non possono essere interpretati come numero |
| Validità | Categoria non ammessa | 2 righe | Rifiutare valori esterni alle sei categorie ammesse |
| Anomalia statistica | Importo strettamente maggiore di tre volte la mediana | 5 righe | Una riga per Vitto, Trasporto, Alloggio, Materiale e Rappresentanza |
| Valutabilità statistica | Categoria con meno di cinque record | 4 righe Formazione | Produrre lo stato `non valutabile statisticamente` e usare il fallback di policy |
| Policy | Sopra soglia con approvatore | 2 righe | Produrre `richiede approvazione` senza non conformità |
| Policy | Sopra soglia senza approvatore | 2 righe | Produrre anche `non conforme: supera soglia senza approvatore assegnato` |

Le quattro righe di `Formazione` comprendono una spesa sopra soglia con approvatore e una sopra soglia senza approvatore. Queste due righe sono incluse rispettivamente nelle quantità dei due scenari di policy.

Per le cinque categorie statisticamente valutabili, distribuzioni e importi saranno costruiti affinché la mediana resti stabile e ciascuna delle cinque righe designate sia strettamente maggiore di tre volte la propria mediana. Le righe con importi mancanti, negativi o non numerici e quelle con categoria mancante o non ammessa non saranno usate per determinare i valori sintetici delle mediane.

## 8. Sovrapposizione degli scenari

Sono previste soltanto queste sovrapposizioni intenzionali:

| Righe coinvolte | Sovrapposizione | Motivo | Segnalazioni attese sulla stessa riga |
|---|---|---|---|
| Formazione sopra soglia con approvatore | Categoria non valutabile e policy | Verificare il fallback alla soglia fissa | `non valutabile statisticamente`; `richiede approvazione` |
| Formazione sopra soglia senza approvatore | Categoria non valutabile e policy senza approvatore | Verificare insieme fallback e non conformità | `non valutabile statisticamente`; `richiede approvazione`; `non conforme: supera soglia senza approvatore assegnato` |
| Ogni membro delle tre coppie con `id_spesa` ripetuto | Due righe condividono lo stesso identificativo | Verificare che l'intera coppia sia riconosciuta | duplicato per `id_spesa` ripetuto |
| Ogni membro delle tre coppie logiche | Due righe descrivono la stessa spesa con identificativi diversi | Verificare il confronto normalizzato | duplicato logico |

Una delle tre coppie logiche userà contemporaneamente spazi esterni e differenze di maiuscole/minuscole in dipendente e categoria, oltre a `,` e `.` come separatori decimali per lo stesso importo. Le altre due coppie useranno valori già uniformi.

Le cinque anomalie statistiche delle categorie valutabili saranno mantenute distinte dai quattro scenari sopra soglia di policy. Gli altri errori intenzionali non si sovrapporranno. In questo modo ogni risultato resterà attribuibile a una regola precisa.

Un campo obbligatorio mancante produrrà la sola segnalazione di completezza relativa a quel campo: le regole di validità saranno applicate ai valori presenti ma malformati. In particolare, un importo mancante non sarà contato anche come non numerico e una categoria mancante non sarà contata anche come non ammessa.

## 9. Ground truth

`data/expected_anomalies.csv` conterrà esattamente queste colonne, nello stesso ordine:

| Colonna | Significato |
|---|---|
| `source_row_number` | Posizione della riga nel CSV principale dopo l'intestazione, partendo da 1 |
| `id_spesa` | Identificativo riportato nella riga sorgente; vuoto quando la segnalazione riguarda l'assenza dell'identificativo |
| `rule_id` | Identificativo stabile della regola che produce la segnalazione |
| `anomaly_type` | Famiglia della segnalazione: completezza, unicità, validità, anomalia statistica, valutabilità statistica, policy o non conformità |
| `field` | Campo interessato; vuoto soltanto per una segnalazione che riguarda complessivamente la riga |
| `expected_status` | Stato deterministico atteso dal controllo |
| `expected_message` | Messaggio deterministico atteso |
| `note` | Spiegazione sintetica dello scenario intenzionale |

Regole di compilazione:

- sarà presente una riga distinta nella ground truth per ogni segnalazione attesa;
- la stessa `source_row_number` comparirà più volte quando una riga deve produrre più segnalazioni;
- `id_spesa` sarà vuoto quando il caso riguarda l'assenza dell'identificativo;
- entrambe le righe di ogni coppia duplicata avranno la propria segnalazione;
- ogni errore intenzionale del CSV principale sarà registrato;
- `rule_id`, `expected_status` ed `expected_message` useranno valori stabili e verificabili;
- l'ordine sarà deterministico: prima `source_row_number`, poi `rule_id`.

Il catalogo minimo dei `rule_id` sarà:

| `rule_id` | `expected_status` | `expected_message` |
|---|---|---|
| `COMPLETENESS_MISSING_ID_SPESA` | `incompleta` | `campo obbligatorio mancante: id_spesa` |
| `COMPLETENESS_MISSING_DATA_SPESA` | `incompleta` | `campo obbligatorio mancante: data_spesa` |
| `COMPLETENESS_MISSING_DIPENDENTE` | `incompleta` | `campo obbligatorio mancante: dipendente` |
| `COMPLETENESS_MISSING_CATEGORIA` | `incompleta` | `campo obbligatorio mancante: categoria` |
| `COMPLETENESS_MISSING_IMPORTO` | `incompleta` | `campo obbligatorio mancante: importo` |
| `COMPLETENESS_MISSING_PROGETTO` | `incompleta` | `campo obbligatorio mancante: progetto` |
| `UNIQUENESS_ID_DUPLICATE` | `duplicato` | `id_spesa duplicato` |
| `UNIQUENESS_LOGICAL_DUPLICATE` | `duplicato logico` | `duplicato logico rilevato` |
| `VALIDITY_NON_NUMERIC_ID` | `non valido` | `id_spesa non numerico` |
| `VALIDITY_INVALID_DATE` | `non valida` | `data_spesa non valida` |
| `VALIDITY_NEGATIVE_AMOUNT` | `non valido` | `importo negativo` |
| `VALIDITY_NON_NUMERIC_AMOUNT` | `non valido` | `importo non numerico` |
| `VALIDITY_INVALID_CATEGORY` | `non valida` | `categoria non ammessa` |
| `STATISTICAL_AMOUNT_ANOMALY` | `anomalia statistica` | `importo superiore a 3 volte la mediana della categoria` |
| `STATISTICAL_NOT_EVALUABLE` | `non valutabile statisticamente` | `categoria con meno di 5 righe` |
| `POLICY_APPROVAL_REQUIRED` | `richiede approvazione` | `richiede approvazione` |
| `POLICY_MISSING_APPROVER` | `non conforme` | `non conforme: supera soglia senza approvatore assegnato` |

La non valutabilità statistica è determinata a livello di categoria. Poiché la ground truth è row-level, `STATISTICAL_NOT_EVALUABLE` sarà registrato per ciascuna delle quattro righe di `Formazione`; le due righe sopra soglia avranno inoltre le segnalazioni di policy definite nella sezione sulle sovrapposizioni.

## 10. Riproducibilità

La futura generazione:

- userà il seed fisso `20260713`;
- produrrà sempre lo stesso ordine delle righe;
- sovrascriverà in modo deterministico i due file generati;
- userà la settimana fissa dal 13/07/2026 al 17/07/2026 e non dipenderà dalla data corrente;
- non effettuerà chiamate esterne;
- non introdurrà errori casuali non registrati nella ground truth;
- produrrà file identici a parità di versione dello script.

## 11. Criteri di accettazione del dataset

1. `data/synthetic_expenses.csv` contiene esattamente le 10 colonne specificate, nello stesso ordine, e nessuna colonna tecnica.
2. Il CSV principale contiene 300 righe di dati.
3. Tutte e sei le categorie valide sono rappresentate.
4. `Formazione` compare in esattamente 4 righe.
5. Tutti gli scenari e tutte le quantità della matrice sono presenti, inclusa una riga con `id_spesa` non numerico.
6. Ogni errore intenzionale corrisponde ad almeno una riga in `data/expected_anomalies.csv`.
7. Ogni record della ground truth corrisponde a una segnalazione intenzionale presente nel CSV principale; le quattro righe di `Formazione` hanno ciascuna una segnalazione `STATISTICAL_NOT_EVALUABLE`.
8. Almeno l'80% delle 300 righe non contiene errori intenzionali.
9. Nomi, codici e contenuti sono interamente sintetici e non riconducibili a persone, aziende o clienti reali.
10. Due generazioni con la stessa versione dello script producono file identici byte per byte.
11. Entrambi i file sono CSV leggibili con strumenti standard.

## 12. Fuori ambito

In questa fase non vengono realizzati:

- motore di validazione;
- dashboard;
- test automatici;
- conversione valutaria;
- database;
- API;
- autenticazione;
- integrazioni con sistemi aziendali.
