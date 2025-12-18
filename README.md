# Open Data 

## Pré 
- Docker
- Docker Compose
- Python 3.9 - 3.10

## Installation

### Télécharger les jars hadoop

Télécharger les jars: https://www.swisstransfer.com/d/e47247eb-3a1e-4022-b29f-1f1f2640ca55
Décompresser les ``jars`` dans un dossier jars à la racine du projet.

### Lancer le docker

Lancer le docker compose via le script start.sh qui initialise les services Docker et lance le job Flink.
```bash
./start.sh
```

### Lancer le producer de données

Lancer le producer de données via le script producer.py.
```bash
python producer.py
```

### Lancer l'API backend

Lancer l'application Flask via le script consumer_backend.py.
```bash
python consumer_backend.py
```

Accéder à l'API backend via l'URL http://localhost:8000.