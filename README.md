# KafkaDemo — Quick Start

Minimal instructions to run the real-time transaction dashboard with Kafka, FastAPI, and a static HTML frontend.

## Prerequisites
- Docker + Docker Compose
- Python 3.11+
- OS: Windows, Linux, or macOS

## 1) Start Infrastructure
```bash
docker-compose up -d
```

## 2) Create and Activate Virtualenv
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

## 3) Install Dependencies
```bash
pip install -r requirements.txt
```

## 4) Start Backend (WebSocket + Serves Front)
Choose based on OS.
```bash
# Windows
uvicorn consumer_backend_windows:app --host 0.0.0.0 --port 8000 --reload

# Linux/macOS
uvicorn consumer_backend_linux:app --host 0.0.0.0 --port 8000 --reload
```

- WebSocket endpoint: `ws://localhost:8000/ws`
- Frontend served at: `http://localhost:8000/`

## 5) Start Producer
```bash
python producer.py
```

## Configuration
- Topic: `events`
- Kafka bootstrap: `localhost:9092`
- Frontend connects dynamically to `${location.host}` for WebSocket

## Troubleshooting (Essentials)
- Port 8000 in use
  - Windows: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`
  - Linux/macOS: `lsof -ti:8000 | xargs kill -9`
- No data on dashboard
  - Ensure producer is running
  - Check backend logs for Kafka errors
  - Verify Docker services: `docker-compose ps`
- WebSocket failure
  - Reload the page (Ctrl+F5)
  - Confirm backend is reachable at `http://localhost:8000/`

## Files
- `producer.py`: generates transactions (LEGIT/FRAUD)
- `consumer_backend_windows.py` / `consumer_backend_linux.py`: WebSocket server
- `index.html`: dashboard UI (Chart.js, logs, distribution, time-window)
- `docker-compose.yml`: Kafka, Zookeeper, Postgres
- `requirements.txt`: Python dependencies
