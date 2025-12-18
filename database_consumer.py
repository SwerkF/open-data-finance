import json
import os
import pg8000.dbapi
from confluent_kafka import Consumer, KafkaError
import time

# config kafka
KAFKA_CONF = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'db-group',
    'auto.offset.reset': 'earliest'
}

#configuration postgres
PG_CONF = {
    "host": "127.0.0.1",
    "port": 5433,
    "database": "transactions_db",
    "user": "user",
    "password": "password"
}

def init_db():
    """initialise la table dans Postgres"""
    try:
        conn = pg8000.dbapi.connect(**PG_CONF)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(50),
                amount FLOAT,
                currency VARCHAR(10),
                status VARCHAR(20),
                timestamp TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("table 'transactions' prête.")
    except Exception as e:
        print(f"Erreur DB: {e}")
        raise e

def main():
    #attente de la disponibilité de la db
    print("tentative de connexion à la base de données...")
    for i in range(10):
        try:
            init_db()
            break
        except Exception:
            print(f"base de donnees non prete, nouvel essai dans 2s... ({i+1}/10)")
            time.sleep(2)
    
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe(['events'])

    print("demarrage du consommateur db...")

    conn = None
    try:
        conn = pg8000.dbapi.connect(**PG_CONF)
        cur = conn.cursor()
        
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            #traitement du message
            data = json.loads(msg.value().decode('utf-8'))
            
            # logique métier : on recupere le statut genere par le producer
            if 'status' in data:
                status = data['status']
            else:
                status = 'FRAUD' if data.get('amount', 0) > 3000 else 'LEGIT'
            
            # insertion en base
            cur.execute("""
                INSERT INTO transactions (transaction_id, amount, currency, status, timestamp)
                VALUES (%s, %s, %s, %s, to_timestamp(%s))
            """, (data['transaction_id'], data['amount'], data['currency'], status, data['timestamp']))
            
            conn.commit()
            print(f"Sauvegardé en base: {data['transaction_id']} ({status})")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
