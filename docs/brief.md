# Esercizio di Valutazione — Candidatura Team Vibe Lab

**Destinatario**: Samuel
**Durata**: 5 giorni lavorativi (una settimana)
**Obiettivo di questo documento**: darti tutto quello che serve per svolgere un esercizio pratico realistico. Non è un test con risposte giuste/sbagliate nascoste — è la simulazione di un vero intervento del Vibe Lab, dall'inizio alla fine.

---

## 1. Perché questo esercizio

Il Vibe Lab è un team interno che riceve richieste da colleghi su progetti cliente e le risolve rapidamente usando strumenti AI (Kiro/Claude), con un metodo strutturato e nel rispetto della policy AI aziendale. Non serve essere un developer perfetto: serve saper **guidare l'AI con metodo**, **verificare criticamente quello che produce**, e **documentare in modo onesto** il valore generato.

Questo esercizio simula un ticket reale che potrebbe arrivare al team. Verrai valutato su come lo affronti, non solo sul risultato finale.

---

## 2. Il caso da risolvere

**Richiesta (fittizia, arrivata via form al Vibe Lab)**:

> "Ogni settimana l'Ufficio Amministrazione riceve un export CSV con le note spese di tutti i dipendenti. Il formato non è sempre pulito: a volte mancano dati, ci sono importi anomali, righe duplicate. Un impiegato oggi passa ~5 ore a settimana a controllare a mano il file, individuare le anomalie e preparare un riepilogo per il CFO. Vorremmo automatizzare questo controllo e avere un piccolo cruscotto che mostri le anomalie della settimana."

**Il tuo compito**: costruire uno strumento che, dato un file di note spese, produca automaticamente un controllo di qualità/anomalie e una visualizzazione riepilogativa.

**Cosa deve controllare lo strumento** (dimensioni minime — puoi proporre di aggiungerne altre se le giustifichi):
- **Completezza**: campi obbligatori mancanti (es. importo, data, categoria, dipendente)
- **Unicità**: righe duplicate (stessa spesa inserita due volte)
- **Validità**: formati errati (date non valide, importi negativi o non numerici)
- **Anomalie di importo**: spese anomale rispetto alla categoria (es. una cena da 800€ quando la media categoria è 40€)
- **Policy check**: spese sopra una soglia per categoria che richiedono approvazione (soglie a tua scelta, documentate)

**Importante**: non esiste un file reale da usare. **Il primo passo del tuo lavoro è generare tu stesso un dataset sintetico** realistico (con errori voluti: null, duplicati, importi anomali, formati sbagliati) usando l'AI. Questo non è un dettaglio secondario — è una regola (vedi §4).

---

## 3. Timeline — 5 giorni

| Giorno | Cosa fare | Consegna di fine giornata |
|---|---|---|
| **1** | Setup ambiente (Kiro/Claude, Git, Python). Analisi requisiti: scrivi le tue domande di chiarimento e mandamele **entro fine giornata** (io rispondo come "richiedente" — dopo questa finestra lavori con quello che hai, come in un caso reale). Genera il dataset sintetico con l'AI. Scrivi `requirements.md` | `requirements.md` + dataset sintetico + domande inviate |
| **2** | Design della soluzione: come struttivi l'analisi (regole, soglie, output), scegli lo stack (es. pandas/duckdb per l'analisi, Streamlit o simile per il cruscotto). Scaffolding del progetto | `design.md` + repo Git inizializzato con struttura |
| **3** | Implementazione delle regole di controllo qualità/anomalie + prime run sul dataset sintetico | Codice funzionante su branch dedicato, prime run |
| **4** | Test (automatici, non solo "provo a occhio"), scan di sicurezza base, code review critica del codice generato dall'AI, cruscotto/dashboard | Test suite + dashboard funzionante + note di review |
| **5** | Documentazione, compilazione case sheet con calcolo della leva, **retrospettiva critica**, demo finale (20 min) | Tutti i deliverable + presentazione |

Puoi redistribuire le ore tra i giorni se ha senso per il tuo modo di lavorare — quello che conta sono le consegne, non l'orario esatto.

---

## 4. Regole del gioco (non negoziabili — riflettono la policy AI reale)

| # | Regola | Perché |
|---|---|---|
| 1 | **Non usare mai dati aziendali o di clienti reali.** Solo il dataset sintetico che generi tu. | È la regola più importante della policy AI Spindox. Nell'esercizio reale, i dati reali cliente non entrano mai nei prompt |
| 2 | **Registra le ore effettive che spendi**, non stimarle a fine settimana. Usa un semplice foglio/tabella con data, ora inizio, ora fine, attività | Senza questo dato, la "leva" che calcolerai a fine esercizio non ha valore |
| 3 | **Ogni commit Git deve indicare se il contenuto è principalmente AI-generated o modificato/scritto da te**, con un messaggio di commit chiaro | Tracciabilità: nel team reale serve per audit e per capire dove l'AI ha davvero aiutato |
| 4 | **Dichiara esplicitamente le assunzioni che fai** dove i requisiti restano ambigui (in un file `ASSUNZIONI.md`) | Nessun caso reale ha requisiti perfetti — la capacità di gestire l'ambiguità è ciò che valutiamo di più |
| 5 | **Non accettare passivamente il codice generato dall'AI.** Per almeno 2 casi durante la settimana, annota (in un file `REVIEW_NOTES.md`) un caso in cui hai corretto, rifiutato o modificato qualcosa che l'AI ha proposto, e perché | È il punto più importante di tutto l'esercizio: un buon "orchestratore" non è chi usa l'AI, è chi la guida e la corregge |

---

## 5. Deliverable richiesti (checklist finale)

- [ ] `requirements.md` — requisiti raccolti, incluse le domande fatte e le risposte ricevute
- [ ] `design.md` — architettura scelta e alternative considerate
- [ ] `ASSUNZIONI.md` — assunzioni dichiarate
- [ ] Dataset sintetico generato (file + breve nota su come l'hai creato)
- [ ] Repository Git con storia dei commit leggibile (non un unico commit finale)
- [ ] Codice funzionante: analisi qualità/anomalie + dashboard/cruscotto
- [ ] Test automatici (anche semplici, ma devono esistere ed essere eseguibili)
- [ ] `REVIEW_NOTES.md` — almeno 2 casi di correzione critica dell'output AI
- [ ] Log ore reali (foglio/tabella)
- [ ] `README.md` — come si esegue il progetto
- [ ] **Case sheet compilato** (template sotto, §6)
- [ ] Retrospettiva scritta (mezza pagina, §7)
- [ ] Demo finale di 20 minuti (venerdì)

---

## 6. Case sheet — da compilare a fine esercizio

Usa lo stesso formato che utilizza il team Vibe Lab su ogni intervento reale:

```
PROBLEMA: [descrizione]
SOLUZIONE: [cosa hai costruito]
STACK: [tool usati]
ORE TUE (con AI): [dal tuo log]
ORE STIMATE SENZA AI: [tua stima motivata — quanto avresti impiegato a fare la stessa cosa senza Kiro/Claude]
LEVA: [ore senza AI / ore con AI]
TRASFERIBILITÀ: [bassa/media/alta — motivata: questo pattern si può riusare altrove?]
CASI DI CORREZIONE AI (min 2): [riassunto da REVIEW_NOTES.md]
```

---

## 7. Retrospettiva (mezza pagina, in linguaggio libero)

Rispondi a queste domande:
1. In quali fasi l'AI ti ha aiutato di più? Perché?
2. In quale momento hai dovuto fermarti e correggere qualcosa che l'AI aveva sbagliato o proposto male?
3. Se dovessi rifare questo esercizio da capo, cosa faresti diversamente?
4. Cosa ti ha reso più difficile la settimana: la parte tecnica, la gestione dell'ambiguità, o altro?

---

## 8. Come verrai valutato

Non stiamo valutando "sai scrivere codice perfetto". Stiamo valutando se hai il profilo giusto per lavorare in un team che usa l'AI con metodo e responsabilità.

| Criterio | Peso | Cosa guardiamo |
|---|---|---|
| **Metodo di lavoro con l'AI** (spec-driven: requisiti → design → codice, non improvvisazione) | 20% | Hai seguito un processo o hai iniziato a scrivere codice senza pensare ai requisiti? |
| **Giudizio critico sull'output AI** | 20% | I 2+ casi di correzione in `REVIEW_NOTES.md` sono reali e ragionati, o generici/inventati a posteriori? |
| **Qualità e mantenibilità del codice** | 15% | Il codice ha test, è leggibile, è organizzato — non solo "funziona una volta" |
| **Rispetto delle regole/governance** | 15% | Dati sintetici rispettati, commit tracciabili, assunzioni dichiarate |
| **Onestà e precisione nella misurazione della leva** | 15% | Le ore sono loggate realmente, la stima "senza AI" è motivata e credibile, non gonfiata |
| **Comunicazione** (domande fatte, documentazione, demo finale) | 15% | Hai fatto domande di chiarimento sensate? La demo è chiara? |

**Cosa NON valutiamo**: l'eleganza estetica della dashboard, la perfezione del codice, la velocità pura di esecuzione.

---

## 9. Strumenti consentiti/suggeriti

| Scopo | Tool | Note |
|---|---|---|
| Agentic IDE | **Kiro** (con Claude) | Stesso strumento usato dal team reale |
| Analisi dati | Python + pandas o duckdb | A tua scelta |
| Dashboard | Streamlit, Plotly Dash, o equivalente leggero | Non serve Superset per questo esercizio — è un ambiente più pesante da configurare, useremo quello vero solo se entri nel team |
| Test | pytest | — |
| Controllo qualità codice base | ruff (lint) + bandit (security lint Python) | Alternative leggere a SonarQube/Snyk, che nel team reale sono già disponibili |
| Versionamento | Git (repo locale o su un tuo account, poi condiviso) | — |

---

## 10. Contatti durante la settimana

- **Domande di chiarimento sul caso** (ruolo "richiedente"): scrivimi entro la fine del Giorno 1 — dopo quella finestra, lavori con quanto raccolto, come in un caso reale
- **Blocchi tecnici/strumenti**: scrivimi in qualsiasi momento, non aspettare di essere bloccato per ore
- **Demo finale**: prenotiamo 20 minuti il Giorno 5 nel pomeriggio

Buon lavoro. L'obiettivo non è che tutto sia perfetto — è che tu dimostri di saper lavorare con metodo, senso critico e onestà su quello che l'AI produce.
