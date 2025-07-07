import socketserver
from typing import List
import socket
import json


#script fastagi para interaccion con las opciones del menu
class FastAGIHandler(socketserver.StreamRequestHandler):

    def handle(self):
        agi_env = {}
        while True:
            line = self.rfile.readline().decode().strip()
            if line == '':
                break
            key, value = line.split(':', 1)
            agi_env[key.strip()] = value.strip()

        self.send_command("ANSWER")
        print("AGI env:", agi_env)

        #capturo los datos que vienen de lado del ami en el canal de llamada
        audios_str = self.get_variable("AUDIOS")
        #captura del numero que se va conectar
        #numero = agi_env.get("agi_callerid", "desconocido")
        numero = agi_env.get("agi_callerid_number") or \
         agi_env.get("agi_callerid") or \
         "UNKNOWN"
        #control en caso no lleguen los audios, porque debe colgar la llamada
        if not audios_str:
            self.send_command('STREAM FILE invalid ""')
            self.send_command("HANGUP")
            return

        #utilizo el separador que debe reconocer para diferenciar entre el uno o el otro nombre y lo coloco en un vector
        audios = audios_str.split('|')

        # Función segura para obtener audios sin romper si faltan elementos
        def safe_get(lst: List[str], idx: int) -> str:
            return lst[idx] if len(lst) > idx else None

        #impresion para controlar cuales son los audios que han venido desde el otro lado
        #esta impresion fue colocada para control
        print(f"[FastAGI] Audios recibidos: {audios}")

        # Reproducir saludo y menú principal
        if audios:
            #le paso que en base al vector, tome el primer nombre y los busque en los audios
            self.send_command(f'STREAM FILE {audios[0]} ""')
            #coloco una espera de un segundo
            self.send_command("WAIT FOR DIGIT 1000")
            #espera de 5 segundos para esperar a que presione una tecla
            lines = self.send_command("WAIT FOR DIGIT 5000")
            #se captura el valor que viene de la respuesta del asterisk
            digit_code = self.get_result_value(lines)
            #captura y conversion del valor para que reconozca adecuadamente el valor
            digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() and int(digit_code) > 0 else None
            print(f"[FastAGI] Tecla recibida: {digit}")

            #dentro de las opciones se maneja al vector, se lo maneja por sus posiciones para enviar al asterisk
            if digit == "1":
                self.enviar_datos_a_socket(numero, "1", "1")
                if audios[1]:
                    #con streamfile le paso al asterisk el nombre y lo busque en su ruta de sonidos
                    self.send_command(f'STREAM FILE {audios[1]} ""')

                lines = self.send_command("WAIT FOR DIGIT 5000")
                digit_code = self.get_result_value(lines)
                digit_sub = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

                if digit_sub == "1" and audios[2]:
                    self.enviar_datos_a_socket(numero, "1_1", "2")
                    self.send_command(f'STREAM FILE {audios[2]} ""')
                elif digit_sub == "2" and audios[3]:
                    self.enviar_datos_a_socket(numero, "1_2", "3")
                    self.send_command(f'STREAM FILE {audios[3]} ""')
                else:
                    self.enviar_datos_a_socket(numero, "99", "9")
                    if audios[9]:
                        self.send_command(f'STREAM FILE {audios[9]} ""')

            elif digit == "2":
                self.enviar_datos_a_socket(numero, "2", "4")
                if audios[4]:
                    self.send_command(f'STREAM FILE {audios[4]} ""')

                lines = self.send_command("WAIT FOR DIGIT 5000")
                digit_code = self.get_result_value(lines)
                digit_sub = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

                if digit_sub == "1" and audios[5]:
                    self.enviar_datos_a_socket(numero, "2_1", "5")
                    self.send_command(f'STREAM FILE {audios[5]} ""')
                elif digit_sub == "2" and audios[6]:
                    self.enviar_datos_a_socket(numero, "2_2", "6")
                    self.send_command(f'STREAM FILE {audios[6]} ""')
                else:
                    self.enviar_datos_a_socket(numero, "999", "9")
                    if audios[9]:
                        self.send_command(f'STREAM FILE {audios[9]} ""')

            elif digit == "3":
                if audios[7]:
                    self.enviar_datos_a_socket(numero, "3", "7")
                    self.send_command(f'STREAM FILE {audios[7]} ""')
                    # Transferir la llamada a otra extensión
                    # Ejemplo: extensión 100 en contexto 'atencion', prioridad 1
                    self.send_command('EXEC Goto default,402,1')
                    self.guardar_paso_extension(numero, "402","7")
                    return  # Importante: salir del handler para no continuar con lógica posterior

            elif digit == "4":
                if audios[8]:
                    self.enviar_datos_a_socket(numero, "4", "8")
                    self.send_command(f'STREAM FILE {audios[8]} ""')
                    
            else:
                if audios[9]:
                    self.enviar_datos_a_socket(numero, "9999", "9")
                    self.send_command(f'STREAM FILE {audios[9]} ""')

        self.send_command("HANGUP")

    def send_command(self, command):
        if not command.endswith('\n'):
            command += '\n'
        self.wfile.write(command.encode())
        self.wfile.flush()

        lines = []
        while True:
            line = self.rfile.readline().decode().strip()
            if line == '':
                break
            lines.append(line)
            if line.startswith('200 result='):
                break
        print(f"Respuesta AGI para '{command.strip()}': {lines}")
        return lines

    def get_variable(self, var_name):
        lines = self.send_command(f'GET VARIABLE {var_name}')
        for line in lines:
            if "result=1" in line:
                value = line.split('(')[-1].rstrip(')')
                return value
        return None

    def get_result_value(self, lines):
        for line in lines:
            if line.startswith("200 result="):
                result = line.split('=')[1].split()[0]
                return result
        return None
    
    #funcion para llamar al script donde se guarda los datos en DB
    def enviar_datos_a_socket(self,numero, opcion, posicion_vect):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 6000))
                payload = json.dumps({
                    'numero': numero,
                    'opcion': opcion,
                    'posicion_vect': posicion_vect
                })
                s.sendall(payload.encode())
                print(f"[Socket] Enviado: {payload}")
        except Exception as e:
            print(f"[ERROR al enviar por socket] {e}")
    
    #funcion para guarda cuando decide comunicarse con otra extension
    def guardar_paso_extension(self, numero, extension, posicion_vect):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 6000))
                payload = json.dumps({
                    'numero': numero,
                    'extension': extension,
                    'posicion_vect': posicion_vect
                })
                s.sendall(payload.encode())
                print(f"[Socket] Enviado paso a extensión: {payload}")
        except Exception as e:
            print(f"[ERROR al enviar paso a extensión por socket] {e}")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    server = ThreadedTCPServer(("192.168.2.10", 4573), FastAGIHandler)
    print("Servidor FastAGI corriendo en puerto 4573 (multicliente)...")
    server.serve_forever()


