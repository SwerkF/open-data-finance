#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

case "$(uname -s 2>/dev/null || true)" in
  MINGW*|MSYS*|CYGWIN*)
    export MSYS_NO_PATHCONV=1
    export MSYS2_ARG_CONV_EXCL='*'
    ;;
esac

COMPOSE=(docker compose)
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
fi

HADOOP_SRC_JAR="jars/flink-shaded-hadoop-3-uber-3.1.1.7.2.9.0-173-9.0.jar"
HADOOP_NOCLI_JAR="jars/flink-shaded-hadoop-3-uber-3.1.1.7.2.9.0-173-9.0-nocli.jar"

if [[ ! -f "$HADOOP_NOCLI_JAR" ]]; then
  if [[ ! -f "$HADOOP_SRC_JAR" ]]; then
    echo "ERREUR: jar Hadoop introuvable: $HADOOP_SRC_JAR" >&2
    exit 1
  fi

  PYTHON_BIN=""
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  fi

  if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERREUR: python/python3 introuvable. Impossible de générer $HADOOP_NOCLI_JAR" >&2
    exit 1
  fi

  echo "→ Génération du jar Hadoop sans commons-cli: $HADOOP_NOCLI_JAR"
  "$PYTHON_BIN" -c "import zipfile; src=r'$HADOOP_SRC_JAR'; dst=r'$HADOOP_NOCLI_JAR'; \
import os; \
try: os.remove(dst)\nexcept FileNotFoundError: pass\n\
with zipfile.ZipFile(src,'r') as zin, zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED) as zout: \
  [zout.writestr(info, zin.read(info.filename)) for info in zin.infolist() if not info.filename.startswith('org/apache/commons/cli/')]; \
print('OK:', dst)"
fi

echo "→ Démarrage des services Docker..."
"${COMPOSE[@]}" up -d --build postgres namenode datanode jobmanager taskmanager zookeeper

echo "→ Attente Zookeeper..."
ZOOKEEPER_NET="$(docker inspect zookeeper --format '{{range $k, $v := .NetworkSettings.Networks}}{{println $k}}{{end}}' | head -n 1)"
if [[ -z "$ZOOKEEPER_NET" ]]; then
  echo "ERREUR: impossible de déterminer le réseau Docker de zookeeper" >&2
  exit 1
fi
for _ in $(seq 1 60); do
  if docker run --rm --network "$ZOOKEEPER_NET" busybox sh -c "nc -zvw 2 zookeeper 2181" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "→ Démarrage Kafka..."
"${COMPOSE[@]}" up -d broker

echo "→ Attente Kafka..."
for _ in $(seq 1 60); do
  # Si le broker a crashé pendant son boot (timeout Zookeeper), on tente de le relancer.
  if ! docker ps --format '{{.Names}}' | grep -qx 'broker'; then
    "${COMPOSE[@]}" up -d broker >/dev/null 2>&1 || true
  fi

  if docker exec broker kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker exec broker kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then
  echo "ERREUR: Kafka n'est pas prêt (broker). Logs broker:" >&2
  docker logs --tail 120 broker || true
  exit 1
fi

echo "→ Attente HDFS..."
for _ in $(seq 1 60); do
  if docker exec namenode hdfs dfs -ls / >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker exec namenode hdfs dfs -ls / >/dev/null 2>&1; then
  echo "ERREUR: HDFS n'est pas prêt (namenode)." >&2
  docker logs --tail 120 namenode || true
  exit 1
fi

echo "→ Création des topics Kafka..."
docker exec broker kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic events --partitions 1 --replication-factor 1 >/dev/null
docker exec broker kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic kpis --partitions 1 --replication-factor 1 >/dev/null

echo "→ Création des dossiers HDFS..."
docker exec namenode hdfs dfs -mkdir -p /logs/fraud /logs/output_volume /logs/output_pays >/dev/null
docker exec namenode hdfs dfs -chmod -R 777 /logs >/dev/null

echo "→ Lancement de flink-job (soumission du job)…"
"${COMPOSE[@]}" up -d --build flink-job

echo ""
echo "- Flink dashboard: http://localhost:8081"
echo "- HDFS: /logs/output_volume, /logs/output_pays"
echo "- Kafka topics: events, kpis"


