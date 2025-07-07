import socketserver
import socket
import json

class FastAGIHandler(socketserver.StreamRequestHandler):

    def handle(self):
        print("[AGI] Conexión recibida...")

        try:
            # Leer variables del entorno AGI hasta una línea vacía
            agi_env = {}
            while True:
                linea = self.rfile.readline().decode().strip()
                if linea == '':
                    break
                if ':' in linea:
                    clave, valor = linea.split(':', 1)
                    agi_env[clave.strip()] = valor.strip()

            # Extraer el argumento desde el request
            agi_request = agi_env.get('agi_request', '')
            if '?' in agi_request:
                _, argumentos_raw = agi_request.split('?', 1)
            else:
                print("[ERROR] No se encontraron argumentos en agi_request")
                return

            print(f"[AGI] Argumentos recibidos: {argumentos_raw}")
            partes = argumentos_raw.split('|')
            if len(partes) < 4:
                print(f"[ERROR] Argumentos incompletos: se esperaban 4, se recibieron {len(partes)}")
                return

            numero, estado, timbrado, hablado = partes[:4]
            self.enviar_datos_a_socket(numero, estado, timbrado, hablado)

        except Exception as e:
            print(f"[ERROR] Fallo al procesar argumentos o enviar datos: {type(e).__name__}: {e}")

    def enviar_datos_a_socket(self, numero, estado, tiempo_timbrado, tiempo_llamada):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect(('localhost', 6010))
                payload = json.dumps({
                    'numero': numero,
                    'estado': estado,
                    'tiempo_timbrado': tiempo_timbrado,
                    'tiempo_llamada': tiempo_llamada,
                })
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
