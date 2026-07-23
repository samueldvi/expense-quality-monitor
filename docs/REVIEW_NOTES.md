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
