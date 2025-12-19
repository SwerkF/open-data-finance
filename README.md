# Open Data 

## Pré 
- Docker
- Docker Compose
- Python 3.9 - 3.10

## Installation

### Changer le formatage de submit_flink_job.sh

Changer le fichier de `CRLF` vers `LF` car possible crash au lancement du job Flink.

### Télécharger les jars hadoop

Télécharger les jars: https://www.swisstransfer.com/d/1759d19c-516c-4682-826a-1346c75aea10
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
