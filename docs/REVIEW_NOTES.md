# Note di revisione critica

## REV-001 — Ambiguità operative residue

**Output AI riesaminato:** l'AI aveva dichiarato che, dopo le risposte di Nicola, non restavano ambiguità.

**Correzione:** la dichiarazione è stata rifiutata perché, pur essendo state chiuse le domande principali, restavano decisioni operative necessarie per rendere i controlli deterministici e testabili.

**Assunzioni aggiunte:**

- criteri per riconoscere valori obbligatori mancanti;
- normalizzazione prima del controllo dei duplicati logici;
- confronto strettamente maggiore per la soglia statistica;
- criteri per considerare assente `approvatore`;
- uso informativo di `valuta_originale` senza conversione;
- file riferito a una singola settimana e dotato dell'intestazione concordata.

## REV-002 — Generatore non conforme e sovra-ingegnerizzato

**Output AI riesaminato:** il primo generatore prodotto dall'AI:

- assegnava tutti e quattro gli scenari sopra soglia alla categoria `Formazione`, mentre la specifica ne prevedeva esattamente uno con approvatore e uno senza approvatore;
- applicava la normalizzazione delle categorie anche al controllo di validità, considerando validi valori con maiuscole, minuscole o spazi diversi dai sei valori esatti comunicati dal richiedente;
- conteneva 870 righe e includeva un secondo motore di rilevamento degli scenari che duplicava gran parte della futura logica di analisi.

**Decisione:** correggere prima la specifica chiarendo le sovrapposizioni intenzionali tra anomalie statistiche e policy; mantenere stretta la validazione delle categorie; nella fase successiva semplificare il generatore eliminando il secondo motore di rilevamento duplicato e conservando soltanto le validazioni strutturali essenziali.

Durante la revisione, l'AI ha inoltre rilevato e rifiutato una successiva istruzione matematicamente incoerente: due righe di categorie statisticamente valutabili avrebbero dovuto superare la soglia di policy restando sotto o uguali a tre volte la mediana, mentre per ciascuna delle stesse categorie era richiesta anche un'anomalia strettamente maggiore di tre volte la mediana. Applicare entrambe le condizioni mantenendo esattamente quattro segnalazioni di policy avrebbe creato segnalazioni aggiuntive. La modifica errata non è stata applicata.

## REV-003 — Gestione incompleta dei tipi pandas

**Output AI riesaminato:** la prima versione del motore verificava alcuni valori parsed confrontandoli soltanto con `None` e neutralizzava le formule CSV soltanto nelle colonne con dtype `object`.

**Problemi rilevati dai test:**

- pandas rappresentava un identificativo non interpretabile come `NaN`, quindi la relativa segnalazione di validità risultava mancante nel confronto con la ground truth;
- con pandas 3 una colonna testuale può usare `StringDtype`, quindi un valore iniziante con `=`, `+`, `-` o `@` non veniva neutralizzato dall'esportazione.

**Correzione:** usare il controllo comune dei valori mancanti anche sui valori parsed e applicare la neutralizzazione a ogni scalare esportato, lasciando invariati i valori non testuali. La soluzione è generale e non contiene eccezioni legate a righe o identificativi del dataset sintetico.

## REV-004 — Revisione avversariale di unicità e controlli Ruff

**Output AI riesaminato:** la prima implementazione richiedeva che `id_spesa` fosse numericamente interpretabile per partecipare al controllo dei duplicati logici e configurava l'esclusione del generatore tramite `tool.ruff.extend-exclude`.

**Problemi rilevati:**

- il design richiede che gli identificativi dei duplicati logici siano presenti e diversi, mentre l'interpretabilità è richiesta per dipendente, data, importo e categoria; due identificativi presenti, distinti ma non numerici devono quindi ricevere sia le segnalazioni di validità sia quelle di duplicato logico;
- `extend-exclude` è globale e sottraeva `scripts/generate_dataset.py` sia al formatter sia al lint, rendendo il controllo Ruff meno ampio del previsto.

**Correzione:** confrontare gli identificativi grezzi presenti per stabilire che siano diversi, mantenendo separata la loro validità numerica; spostare l'esclusione del generatore in `tool.ruff.format.exclude`, così il file resta incluso nel lint e nella scansione Bandit. Test avversariali indipendenti dal dataset completo verificano entrambe le correzioni.

## REV-005 — Conflitto tra colonna aggiuntiva e numero di riga tecnico

**Problema rilevato:** il loader ammetteva in generale le colonne aggiuntive, ma falliva con un `ValueError` non applicativo quando il CSV conteneva una colonna extra chiamata `source_row_number`. Il nome entrava in conflitto con la colonna tecnica aggiunta dopo il caricamento.

**Correzione:** prima di aggiungere la numerazione tecnica, l'eventuale colonna in ingresso con lo stesso nome viene conservata con un nome suffissato non ambiguo. Un test di regressione verifica sia la numerazione tecnica sia la conservazione del valore originale.
