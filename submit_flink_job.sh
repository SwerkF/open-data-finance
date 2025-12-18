#!/usr/bin/env bash
set -euo pipefail

echo "Attente du JobManager (http://jobmanager:8081) ..."
for i in $(seq 1 120); do
  if curl -sf "http://jobmanager:8081/overview" >/dev/null 2>&1; then
    echo "JobManager prêt."
    break
  fi
  sleep 2
done

echo "Soumission du job PyFlink au cluster (detached) ..."
/opt/flink/bin/flink run -m jobmanager:8081 -d -py /app/flink_kpi.py

echo "Job soumis. Je garde le conteneur vivant pour pouvoir consulter les logs."
tail -f /dev/null


