# archivo: registrar_tecla.py

import socket
import json
import psycopg2
from datetime import datetime
from psycopg2 import sql
import threading

HOST = 'localhost'
PORT = 6000

def guardar_interaccion(numero, opcion, posicion_vect):
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
            INSERT INTO carpeta_llamadas_interaccionllamada (numero, opcion, posicion_vect, created_at)
            VALUES (%s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (numero, opcion, posicion_vect, datetime.now()))
        conn.commit()
        print(f"[OK] Guardado: {numero}, {opcion}, {posicion_vect}")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

def guardar_paso_extension(numero, extension, posicion_vect):
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
            INSERT INTO carpeta_llamadas_pasoextension (numero, extension, posicion_vect, created_at)
            VALUES (%s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (numero, extension, posicion_vect, datetime.now()))
        conn.commit()
        print(f"[OK] Paso a extensión guardado: {numero} → {extension}")
    except Exception as e:
        print(f"[ERROR al guardar paso a extensión] {e}")
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

            if 'opcion' in datos and 'posicion_vect' in datos:
                # Guardar interacciones del IVR
                opcion = datos.get('opcion')
                posicion = datos.get('posicion_vect')
                guardar_interaccion(numero, opcion, posicion)

            elif 'extension' in datos and 'posicion_vect' in datos:
                extension = datos.get('extension')
                posicion = datos.get('posicion_vect')
                guardar_paso_extension(numero, extension, posicion)

            else:
                print(f"[ERROR] Datos no reconocidos: {datos}")

        except json.JSONDecodeError:
            print(f"[ERROR] JSON inválido: {data}")
        except Exception as e:
            print(f"[ERROR al procesar datos] {e}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Servidor escuchando en {HOST}:{PORT}...")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

# Esto evita que se ejecute al importar desde otro script
if __name__ == "__main__":
    print("servidor para guardad datos en DB, activo...")
    main()
