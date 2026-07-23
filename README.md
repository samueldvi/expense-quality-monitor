# expense-quality-monitor

Progetto per ridurre il controllo manuale settimanale degli export CSV delle note spese, che possono contenere dati mancanti, duplicati, valori non validi, importi anomali e spese soggette a policy.

## Stato attuale

I requisiti sono stati consolidati, il dataset sintetico è stato progettato e il generatore deterministico è stato implementato. Il motore di analisi, i test e la dashboard non sono ancora implementati.

## Dati

Il progetto deve utilizzare esclusivamente dati sintetici. Non sono ammessi dati aziendali o di clienti reali, inclusi i prompt inviati agli strumenti AI.

## Generazione dei dataset

```bash
python3 scripts/generate_dataset.py
```

Il comando produce:

- `data/synthetic_expenses.csv`;
- `data/expected_anomalies.csv`.

La generazione crea 300 righe usando il seed fisso `20260713` e una settimana sintetica fissa. Il secondo file contiene la ground truth delle anomalie introdotte intenzionalmente. A parità di versione dello script, gli output sono riproducibili.

## Struttura attuale

```text
.
├── .gitignore
├── README.md
├── TIME_LOG.md
├── data
│   ├── expected_anomalies.csv
│   └── synthetic_expenses.csv
├── docs
    ├── ASSUNZIONI.md
    ├── REVIEW_NOTES.md
    ├── brief.md
    ├── dataset.md
    └── requirements.md
└── scripts
    └── generate_dataset.py
```

## Convenzione dei commit

I messaggi di commit dovranno iniziare con uno dei prefissi:

- `human:` per contenuto principalmente scritto o modificato dalla persona;
- `ai-generated:` per contenuto principalmente generato dall'AI;
- `ai-assisted:` per contenuto realizzato dalla persona con assistenza AI.
