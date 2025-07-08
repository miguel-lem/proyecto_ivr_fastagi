#acript que se encarga de funcionar como fastagi pero de control en caso de que no contesten la llamada
#y controlar los tiempos de timbrado
import socketserver
import socket
import json

class FastAGIHandler(socketserver.StreamRequestHandler):

    def handle(self):
        print("[AGI] Conexión recibida...")

        try:
            # Leer variables del entorno AGI hasta una línea vacía
            #se crea un diccionario
            agi_env = {}
            while True:
                #se lee linea por linea a "rfile" el canal de entrada de AGI
                linea = self.rfile.readline().decode().strip()
                #cuando encuentra un espacio eso indica que es un fin y debe saltar
                if linea == '':
                    break
                #si la linea tiene dos puntos se cosidera argumento valido
                if ':' in linea:
                    #divide los campos en clave valor y los guarda en el diccionario
                    clave, valor = linea.split(':', 1)
                    agi_env[clave.strip()] = valor.strip()

            # Extraer el argumento desde el request
            agi_request = agi_env.get('agi_request', '')
            #separa lo que este a continuacion de "?"
            if '?' in agi_request:
                _, argumentos_raw = agi_request.split('?', 1)
            else:
                #si no hay argumentos devuelve un error
                print("[ERROR] No se encontraron argumentos en agi_request")
                return

            print(f"[AGI] Argumentos recibidos: {argumentos_raw}")
            #se separan los argumentos que estan con "|"
            partes = argumentos_raw.split('|')
            #controla que vengan 4 argumentos, esta parte se puede modificar si entreso se necesita mas datos
            if len(partes) < 4:
                print(f"[ERROR] Argumentos incompletos: se esperaban 4, se recibieron {len(partes)}")
                return

            #extraccion de los 4 primeros elementos de una lista y colocado en variables
            numero, estado, timbrado, hablado = partes[:4]
            #paso los parametros a la funcion que envia los datos hacia el guardado en DB
            self.enviar_datos_a_socket(numero, estado, timbrado, hablado)

        #atrapado de error
        except Exception as e:
            print(f"[ERROR] Fallo al procesar argumentos o enviar datos: {type(e).__name__}: {e}")

    #funcion para enviar los datos al script que se conecta con la DB
    def enviar_datos_a_socket(self, numero, estado, tiempo_timbrado, tiempo_llamada):
        try:
            #inicio del socket "with", se asegura de cortar el proceso en caso de fallo
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                #colocacion de localhost y de puerto, este puerto es importante que no se repita para evitar conflicto
                s.connect(('localhost', 6010))
                #preparo el json
                payload = json.dumps({
                    'numero': numero,
                    'estado': estado,
                    'tiempo_timbrado': tiempo_timbrado,
                    'tiempo_llamada': tiempo_llamada,
                })
                #convierto a bytecode y envio los datos
                s.sendall(payload.encode())
                print(f"[Socket] Enviado: {payload}")
        except Exception as e:
            print(f"[ERROR al enviar por socket] {type(e).__name__}: {e}")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    server = ThreadedTCPServer(("192.168.2.10", 4574), FastAGIHandler)
    print("[AGI Server] Servidor FastAGI corriendo en puerto 4574...")
    server.serve_forever()
