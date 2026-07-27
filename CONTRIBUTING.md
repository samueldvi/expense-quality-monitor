# Contribuire

## Lingua del repository

- documentazione, interfaccia e comunicazione di progetto sono in italiano;
- variabili, funzioni, classi, moduli e file Python usano nomi in inglese;
- i termini tecnici standard mantengono la forma più comune;
- titoli e descrizioni delle Pull Request e messaggi di commit sono in italiano;
- la convenzione si applica al nuovo lavoro e non richiede di riscrivere la cronologia esistente.

## Flusso di lavoro

1. partire da `main` aggiornato;
2. creare un branch dedicato alla modifica;
3. mantenere le modifiche limitate e coerenti con l’obiettivo;
4. eseguire test e controlli di qualità;
5. revisionare il diff completo;
6. aprire una Pull Request;
7. effettuare il merge soltanto con CI verde e revisione completata.

## Nomi dei branch

Usare un prefisso tecnico e una descrizione leggibile:

- `feature/...` per nuove funzionalità;
- `fix/...` per correzioni;
- `docs/...` per documentazione;
- `chore/...` per manutenzione.

## Messaggi di commit

Usare Conventional Commits con una descrizione in italiano. Il tipo dipende dal contenuto
della modifica, non dallo strumento usato per realizzarla.

```text
docs: chiarisce il posizionamento del prodotto
fix: corregge la lettura dei CSV con BOM
test: aggiunge casi per gli schemi incompatibili
chore: aggiorna i controlli del repository
```

L’assistenza AI non richiede un prefisso dedicato.

## Pull Request

Titolo e descrizione devono essere in italiano. La descrizione riporta:

- obiettivo;
- modifiche principali;
- verifiche eseguite;
- eventuali limiti o rischi;
- impatto su documentazione, dati o comportamento.

## Uso dell’AI

L’AI può supportare analisi, implementazione, refactoring, generazione di test e revisione
della documentazione. Non sostituisce la definizione dei requisiti, le decisioni
architetturali, la verifica dei risultati, la revisione del diff o la responsabilità sul
codice accettato.

## Human-in-the-loop

Il processo prevede:

1. definizione umana dell’obiettivo e dei vincoli;
2. proposta o modifica assistita;
3. revisione manuale del diff;
4. esecuzione di test, lint, format e controlli di sicurezza;
5. correzione delle anomalie rilevate;
6. approvazione umana prima del commit e del merge.

## Controlli richiesti

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m bandit -r src app.py -c pyproject.toml
git diff --check
```
