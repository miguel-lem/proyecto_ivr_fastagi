# archivo: registrar_tecla.py
#este script es para conectarse con socket hacia el servidor donde esta la db y asi
#guardar los datos de las interacciones de las llamadas
import socket
import json
import psycopg2
from datetime import datetime
from psycopg2 import sql
import threading

#el host depende si se esta trabajando en local o en remoto
HOST = 'localhost'
PORT = 6000

#creo la funcion que permitira con el uso del query, guardar los datos en la tabla
def guardar_interaccion(numero, opcion, posicion_vect):
    try:
        #genero la conexion hacia la db, los datos internos ya son muy conocidos de como llenar
        conn = psycopg2.connect(
            host="192.168.2.18",
            port=5432,
            dbname="ivruno",
            user="postgres",
            password="mi_contrasena"
        )
        #creo un cursor para establecer la conexion
        cursor = conn.cursor()
        #genero la sentencia sql que se utilizara
        insert_query = sql.SQL("""
            INSERT INTO carpeta_llamadas_interaccionllamada (numero, opcion, posicion_vect, created_at)
            VALUES (%s, %s, %s, %s)
        """)
        #ejecuto el cursos y le paso el query creado
        cursor.execute(insert_query, (numero, opcion, posicion_vect, datetime.now()))
        #confirmamos el guardado
        conn.commit()
        #impresion en caso que todo se guarde bien
        print(f"[OK] Guardado: {numero}, {opcion}, {posicion_vect}")
    except Exception as e:
        #impresion de error en caso que lo capture
        print(f"[ERROR] {e}")
    finally:
        #proceso final para cerrar la conexion al terminar el trabajo
        if conn:
            cursor.close()
            conn.close()

#funcion para guardar datos, maneja la misma logica que la anterior, solo que enfocada en otra tabla
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

#funcion creada para separar las logicas de cual funcion de guardado se debe utilizar
def handle_client(conn, addr):
    #asegurar que la conexion se cierre al final
    with conn:
        try:
            #puede recibir hasta 1024 bytes desde el cliente y los decodifica a texto
            data = conn.recv(1024).decode()
            #cargar el string como un objeto JSON
            datos = json.loads(data)
            #capturar el número de teléfono que es un campo comun que recibe del otro lado
            numero = datos.get('numero')

            #si entre las variables esta "opcion", quiere decir que pertenece a esta determinada tabla
            if 'opcion' in datos and 'posicion_vect' in datos:
                # Guardar interacciones del IVR
                opcion = datos.get('opcion')
                posicion = datos.get('posicion_vect')
                guardar_interaccion(numero, opcion, posicion)

            #esta parte seria cuando pase la llamada a otra extension
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
    #preparo el socket para que escuche
    #el with es para asegurarse que se cierre si se produce algun error
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        #el bind es para controlar que se le pase una ip y el puerto en el cual trabajara
        server.bind((HOST, PORT))
        #coloca el socket en modo escucha
        server.listen()
        #lazar una impresion informando que esta esuchando en el puerto
        print(f"Servidor escuchando en {HOST}:{PORT}...")

#genera una conexion bloqueante
        while True:
            conn, addr = server.accept()
            #crea un hilo para cada conexion
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

# Esto evita que se ejecute al importar desde otro script
#es decir, si lo importamos desde otro script solo funcionara llamando de manera individual a las funciones,
#de esa manera se proteje las funciones 
if __name__ == "__main__":
    print("servidor para guardar datos de interaccion en DB escuchando en el puerto 6000, activo...")
    main()
