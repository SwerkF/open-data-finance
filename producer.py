from confluent_kafka import Producer
import json
import time
import random
from datetime import datetime

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
topic = 'events'

NB_CLIENTS = 1000
CURRENCIES = {
    "FR": "EUR", "US": "USD", "GB": "GBP", "JP": "JPY", "BR": "BRL"
}
COUNTRIES = list(CURRENCIES.keys())

user_state = {}

def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))

def get_timestamp():
    return time.time()

def generate_data(tx_num):
    account_id = random.randint(1, NB_CLIENTS)
    
    if account_id not in user_state:
        user_state[account_id] = {
            "pays": "FR",
            "habitudes_montant": random.randint(20, 100)
        }
    
    current_user = user_state[account_id]
    
    random_number = random.random()
    
    pays = current_user["pays"]
    montant = 0
    scenario = "Normal"

    if random_number < 0.02:
        scenario = "Fraude_Voyage"
        available_countries = [c for c in COUNTRIES if c != current_user["pays"]]
        pays = random.choice(available_countries)
        montant = random.gauss(current_user["habitudes_montant"], 10)

    elif random_number < 0.04:
        scenario = "Fraude_Montant"
        pays = current_user["pays"]
        montant = current_user["habitudes_montant"] * random.randint(50, 100)

    else:
        pays = current_user["pays"]
        montant = random.gauss(current_user["habitudes_montant"], 10)

    montant = abs(int(montant)) + 1
    devise = CURRENCIES[pays]
    
    user_state[account_id]["pays"] = pays

    if scenario != "Normal":
        print(f"Génération {scenario} | Compte: {account_id} | {pays} | {montant} {devise}")

    return {
        "transaction_id": f"TX-{tx_num}",
        "account_id": account_id,
        "amount": montant,
        "currency": devise,
        "country": pays,
        "timestamp": get_timestamp(),
        "status": "FRAUD" if scenario != "Normal" else "LEGIT"
    }

try:
    transaction_counter = 100000
    while True:
        producer.poll(0)

        data = generate_data(transaction_counter)
        transaction_counter += 1

        producer.produce(topic, json.dumps(data).encode('utf-8'), callback=delivery_report)
        
        time.sleep(0.01) 

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur.")
finally:
    print("Vidage du buffer Kafka.")
    producer.flush()