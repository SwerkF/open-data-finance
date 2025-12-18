from confluent_kafka import Producer
import json
import time
import random
from datetime import datetime

# config kafka
conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)
topic = 'events' # nom du topic cohérent avec le projet

# config metier
NB_CLIENTS = 1000   # on simule 1000 clients qui reviennent
CURRENCIES = {
    "FR": "EUR", "US": "USD", "GB": "GBP", "JP": "JPY", "BR": "BRL"
}
COUNTRIES = list(CURRENCIES.keys())

# Mémoire de l'état des clients pour la cohérence des fraudes
# Structure : { id_compte : { "pays": "FR", "habitudes_montant": 50 } }
user_state = {}

def delivery_report(err, msg):
    """ Rapport de livraison. 
    Pour éviter de spammer la console si on envoie vite, on affiche seulement les erreurs
    ou une confirmation de temps en temps. """
    if err is not None:
        print('Message delivery failed: {}'.format(err))

def get_timestamp():
    return time.time()

def generate_data(tx_num):
    # selection d'un client existant ou nouveau
    account_id = random.randint(1, NB_CLIENTS)
    
    # initialisation si c'est la premiere fois qu'on voit ce client
    if account_id not in user_state:
        user_state[account_id] = {
            "pays": "FR", #tout le monde commence en france pour simplifier
            "habitudes_montant": random.randint(20, 100) #montant moyen habituel
        }
    
    current_user = user_state[account_id]
    
    # determination du scénario (Normal vs Fraude)
    dice = random.random()
    
    pays = current_user["pays"]
    montant = 0
    scenario = "Normal"

    # scenario 1 : fraude voyage (2% de chance)
    # le client change de pays instantanement par rapport à la derniere fois
    if dice < 0.02:
        scenario = "Fraude_Voyage"
        available_countries = [c for c in COUNTRIES if c != current_user["pays"]]
        pays = random.choice(available_countries)
        # Montant normal
        montant = random.gauss(current_user["habitudes_montant"], 10)

    # scenario 2 : fraude montant (2% de chance)
    # le montant est 50x à 100x supérieur à la moyenne habituelle
    elif dice < 0.04:
        scenario = "Fraude_Montant"
        pays = current_user["pays"]
        montant = current_user["habitudes_montant"] * random.randint(50, 100)

    # scenario 3 : normal (96% de chance)
    else:
        pays = current_user["pays"]
        montant = random.gauss(current_user["habitudes_montant"], 10)

    # nettoyage des données
    montant = abs(int(montant)) + 1
    devise = CURRENCIES[pays]
    
    # mise à jour de la mémoire pour la prochaine transaction de ce client
    user_state[account_id]["pays"] = pays

    # affichage console pour voir les fraudes passer (optionnel)
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
        
        # simulation de débit (0.01 = 100 messages/seconde)
        time.sleep(0.01) 

except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur.")
finally:
    # on attend que tous les messages soient bien partis avant de couper
    print("Vidage du buffer Kafka (flush)...")
    producer.flush()