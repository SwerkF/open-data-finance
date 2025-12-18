FROM flink:1.17.0-java11

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev curl && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY flink_kpi.py .
COPY jars/ ./jars/

COPY submit_flink_job.sh /app/submit_flink_job.sh
RUN chmod +x /app/submit_flink_job.sh

CMD ["/bin/bash", "/app/submit_flink_job.sh"]