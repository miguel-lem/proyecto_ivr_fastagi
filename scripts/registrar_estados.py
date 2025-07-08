# archivo: guardar_estados_llamada.py
#este script fue diseñado para poder guardar los registros de eventos que suceden
#previos a que funcione el fastagi del ivr,
#es decir este puede capturar cosas como si no se contesta
import socket
import json
import psycopg2
from datetime import datetime
from psycopg2 import sql
import threading

HOST = 'localhost'
PORT = 6010  # Puerto que se coloco, este evita chocarse con el del otro script que tambien guarda datos

def guardar_estado_llamada(numero, estado, tiempo_timbrado, tiempo_llamada):
    try:
        conn = psycopg2.connect(
            host="192.168.2.18",
            port=5432,
            dbname="ivruno",
            user="postgres",
            password="mi_contrasena"
        )
        cursor = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO carpeta_llamadas_estadosllamada (numero, estado, tiempo_timbrado, tiempo_llamada, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (numero, estado, tiempo_timbrado, tiempo_llamada, datetime.now()))
        conn.commit()
        print(f"[OK] Estado guardado: {numero}, {estado}, timbrado: {tiempo_timbrado}, llamada: {tiempo_llamada}")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def handle_client(conn, addr):
    with conn:
        try:
            data = conn.recv(1024).decode()
            datos = json.loads(data)

            numero = datos.get('numero')
            estado = datos.get('estado')
            timbrado = datos.get('tiempo_timbrado', '0')
            hablado = datos.get('tiempo_llamada', '0')

            if numero and estado:
                guardar_estado_llamada(numero, estado, timbrado, hablado)
            else:
                print(f"[ERROR] Faltan datos requeridos: {datos}")

        except json.JSONDecodeError:
            print(f"[ERROR] JSON inválido: {data}")
        except Exception as e:
            print(f"[ERROR al procesar datos] {e}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Servidor de estados de llamada escuchando en {HOST}:{PORT}...")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    print("Servidor para guardar estados de llamadas activo...")
    main()
