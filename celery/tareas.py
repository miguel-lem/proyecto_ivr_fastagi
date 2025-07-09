# tareas.py
#este script es para crear celery, el cual se encargara de ejecutar las tareas en segundo plano
from celery import Celery
import requests

app = Celery('mi_script', broker='amqp://guest:guest@192.168.2.18:5672//')

@app.task
def enviar_datos(channel,exten):
    url = 'http://localhost:8000/api/llamadas/realizar_llamadaunica/'

    payload = {
        "channel": channel,
        "exten": exten,
        "context": "default",
        "priority": 1,
        "callerid": "Mi llamada",
        "numero_celular": channel
    }

    try:
        respuesta = requests.post(url, json=payload)
        print("Respuesta de la API:", respuesta.status_code, respuesta.text)
        return respuesta.json()
    except Exception as e:
        print("Error al enviar datos:", e)
        return {"error": str(e)}





