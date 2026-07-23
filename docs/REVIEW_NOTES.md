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
