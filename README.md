# expense-quality-monitor

Progetto per ridurre il controllo manuale settimanale degli export CSV delle note spese, individuando problemi di qualità, anomalie e casi soggetti a policy.

## Stato attuale

Il repository è nella fase iniziale di analisi e setup. I chiarimenti iniziali del richiedente sono stati ricevuti e i requisiti sono stati consolidati. Il design e l'implementazione non sono ancora iniziati; il motore di analisi, il dataset sintetico, i test e la dashboard non esistono ancora.

## Dati

Il progetto deve utilizzare esclusivamente dati sintetici. Non sono ammessi dati aziendali o di clienti reali, inclusi i prompt inviati agli strumenti AI.

## Struttura attuale

```text
.
├── .gitignore
├── README.md
├── TIME_LOG.md
└── docs
    ├── ASSUNZIONI.md
    ├── brief.md
    └── requirements.md
```

## Convenzione dei commit

I messaggi di commit dovranno iniziare con uno dei prefissi:

- `human:` per contenuto principalmente scritto o modificato dalla persona;
- `ai-generated:` per contenuto principalmente generato dall'AI;
- `ai-assisted:` per contenuto realizzato dalla persona con assistenza AI.

In questa attività non viene creato alcun commit.
