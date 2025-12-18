import asyncio
import json
from fastapi import FastAPI, WebSocket
from aiokafka import AIOKafkaConsumer
import uvicorn

app = FastAPI()

KAFKA_TOPIC = "events"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="my-group"
    )
    
    await consumer.start()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode('utf-8'))
            
            #logique de detection de fraude
            #on fait confiance au producer qui a genere la donnee
            if 'status' not in data:
                data['status'] = 'FRAUD' if data['amount'] > 3000 else 'LEGIT'

            if data['status'] == 'FRAUD':
                print(f"ALERTE FRAUDE: {data['amount']} EUR")
            
            await websocket.send_json(data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
