# Case sheet — Expense Quality Monitor

PROBLEMA:
L'Ufficio Amministrazione riceve un CSV settimanale delle note spese che può contenere campi obbligatori mancanti, valori non validi, duplicati, importi anomali e spese soggette a policy. Serve produrre un riepilogo strutturato per il CFO. Nel caso fittizio il brief descrive circa cinque ore settimanali di controllo manuale: è un dato del brief, non un risultato misurato dal progetto.

SOLUZIONE:
Un dataset sintetico deterministico con ground truth, un motore di controlli per completezza, validità, unicità, anomalie statistiche e policy, una dashboard Streamlit con segnalazioni, metriche, riepiloghi e filtri, un export CSV, test automatici e una CI GitHub Actions.

STACK:
Python; pandas; Streamlit; pytest; Ruff; Bandit; Git; GitHub Actions; Codex; ChatGPT.

ORE TUE (con AI):
12h 44m complessive nette: 9h 00m il 23/07/2026 e 3h 44m il 24/07/2026.

ORE STIMATE SENZA AI:
18 ore. La stima considera il maggiore tempo necessario per definire le regole, implementare la soluzione, creare dataset e ground truth, preparare test, dashboard e CI, svolgere le revisioni e completare la documentazione.

LEVA:
Circa 1,41×, calcolata come `18,0 / 12,7333`.

### Lettura critica della leva

La leva di 1,41× è inferiore rispetto a quella ottenibile in attività prevalentemente generative. In questo esercizio una parte significativa del tempo è stata dedicata alla definizione e alla verifica dei requisiti, alla costruzione della ground truth, al controllo delle sovrapposizioni tra regole, alla revisione dei diff e all'esecuzione di verifiche deterministiche.

L'AI ha supportato analisi, implementazione, test, refactoring e documentazione, ma requisiti e vincoli sono stati verificati dall'autore e ogni output è stato esaminato prima dell'accettazione. Test e controlli hanno permesso di individuare e correggere anomalie e incoerenze, mantenendo umana la responsabilità finale. La leva rappresenta quindi una stima del tempo risparmiato: non misura la qualità, la quantità di codice prodotto o il livello di autonomia dello strumento.

Nei lavori con requisiti ambigui e necessità di tracciabilità, il contributo dell'AI comprende anche l'esplorazione di alternative, l'individuazione di incoerenze e la preparazione di verifiche ripetibili, non soltanto la generazione di contenuti.

TRASFERIBILITÀ:
Alta. Il pattern loader → normalizzazione → regole → pipeline → reporting → dashboard può essere adattato ad altri controlli deterministici su file tabellari; le regole specifiche del dominio devono essere ridefinite. Non è stato ancora riutilizzato in altri progetti.

CASI DI CORREZIONE AI:

- `REV-001`: l'AI aveva dichiarato chiuse tutte le ambiguità; sono state esplicitate le assunzioni operative ancora necessarie.
- `REV-002`: il primo generatore distribuiva in modo errato gli scenari di policy, rendeva valide categorie malformate ed era sovra-ingegnerizzato; specifica e generatore sono stati corretti.
- `REV-003`: test e ground truth hanno rilevato una gestione incompleta di `NaN` e `StringDtype`; i controlli dei valori mancanti e l'export sono stati resi generali.
- `REV-004`: la regola dei duplicati logici richiedeva erroneamente ID numerici e Ruff escludeva il generatore anche dal lint; semantica e configurazione sono state corrette.
- `REV-006`: lo smoke test ha rilevato la telemetria predefinita di Streamlit; la raccolta delle statistiche d'uso è stata disabilitata.
