# archivo: registrar_interaccion.py

import psycopg2
from psycopg2 import sql
from datetime import datetime

def guardar_interaccion(numero: str, opcion: str, posicion_vect: str):
    try:
        conn = psycopg2.connect(
            host="192.168.2.18",          # o IP del contenedor si es distinto
            port=5432,                 # el puerto del contenedor
            dbname="ivruno",
            user="postgres",
            password="mi_contrasena"
        )
        cursor = conn.cursor()

        insert_query = sql.SQL("""
            INSERT INTO tu_app_interaccionllamada (numero, opcion, posicion_vect, created_at)
            VALUES (%s, %s, %s, %s)
        """)

        cursor.execute(insert_query, (numero, opcion, posicion_vect, datetime.now()))
        conn.commit()
        print("Interacción guardada exitosamente")

    except Exception as e:
        print(f"Error al guardar interacción: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
