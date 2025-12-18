import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from aiokafka import AIOKafkaConsumer
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

KAFKA_TOPIC = "events"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/")
async def get():
    return FileResponse("web/index.html")

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
            
            # LOGIQUE DE DÉTECTION DE FRAUDE
            # On fait confiance au producer qui a généré la donnée
            # Si le champ status est manquant (vieux messages), on le recalcule
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
