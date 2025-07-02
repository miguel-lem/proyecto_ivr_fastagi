import socketserver
from typing import List
from registrar_tecla import guardar_interaccion




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
                if audios[1]:
                    #con streamfile le paso al asterisk el nombre y lo busque es su ruta de sonidos
                    self.send_command(f'STREAM FILE {audios[1]} ""')

                lines = self.send_command("WAIT FOR DIGIT 5000")
                digit_code = self.get_result_value(lines)
                digit_sub = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

                if digit_sub == "1" and audios[2]:
                    self.send_command(f'STREAM FILE {audios[2]} ""')
                elif digit_sub == "2" and audios[3]:
                    self.send_command(f'STREAM FILE {audios[3]} ""')
                else:
                    if audios[9]:
                        self.send_command(f'STREAM FILE {audios[9]} ""')

            elif digit == "2":
                if audios[4]:
                    self.send_command(f'STREAM FILE {audios[4]} ""')

                lines = self.send_command("WAIT FOR DIGIT 5000")
                digit_code = self.get_result_value(lines)
                digit_sub = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

                if digit_sub == "1" and audios[5]:
                    self.send_command(f'STREAM FILE {audios[5]} ""')
                elif digit_sub == "2" and audios[6]:
                    self.send_command(f'STREAM FILE {audios[6]} ""')
                else:
                    if audios[9]:
                        self.send_command(f'STREAM FILE {audios[9]} ""')

            elif digit == "3":
                if audios[7]:
                    self.send_command(f'STREAM FILE {audios[7]} ""')
                    # Transferir la llamada a otra extensión
                    # Ejemplo: extensión 100 en contexto 'atencion', prioridad 1
                    self.send_command('EXEC Goto default,402,1')
                    return  # Importante: salir del handler para no continuar con lógica posterior

            elif digit == "4":
                if audios[8]:
                    self.send_command(f'STREAM FILE {audios[8]} ""')
                    
            else:
                if audios[9]:
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


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    server = ThreadedTCPServer(("192.168.2.10", 4573), FastAGIHandler)
    print("Servidor FastAGI corriendo en puerto 4573 (multicliente)...")
    server.serve_forever()



#############################################################
'''class FastAGIHandler(socketserver.StreamRequestHandler):

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

        audios_str = self.get_variable("AUDIOS")
        if not audios_str:
            self.send_command('STREAM FILE invalid ""')
            self.send_command("HANGUP")
            return

        ###audios = audios_str.split(',')
        audios = audios_str.split('|')

        # Función segura para obtener audios sin romper si faltan elementos
        def safe_get(lst: List[str], idx: int) -> str:
            return lst[idx] if len(lst) > idx else None

        saludo = safe_get(audios, 0)
        opcion1 = safe_get(audios, 1)
        subopcion_1_1 = safe_get(audios, 2)
        subopcion_1_2 = safe_get(audios, 3)
        opcion2 = safe_get(audios, 4)
        subopcion_2_1 = safe_get(audios, 5)
        subopcion_2_2 = safe_get(audios, 6)
        opcion3 = safe_get(audios, 7)
        opcion4 = safe_get(audios, 8)
        opcion_invalida = safe_get(audios, 9)

        print(f"[FastAGI] Audios recibidos: {audios}")

        # Reproducir saludo y menú principal
        if saludo:
            self.send_command(f'STREAM FILE {saludo} ""')
            self.send_command("WAIT FOR DIGIT 1000")

            lines = self.send_command("WAIT FOR DIGIT 5000")
            digit_code = self.get_result_value(lines)
            digit = chr(int(digit_code)) if digit_code and digit_code.isdigit() and int(digit_code) > 0 else None
            print(f"[FastAGI] Tecla recibida: {digit}")

            if digit == "1":
                if opcion1:
                    self.send_command(f'STREAM FILE {opcion1} ""')

                lines = self.send_command("WAIT FOR DIGIT 5000")
                digit_code = self.get_result_value(lines)
                digit_sub = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

                if digit_sub == "1" and subopcion_1_1:
                    self.send_command(f'STREAM FILE {subopcion_1_1} ""')
                elif digit_sub == "2" and subopcion_1_2:
                    self.send_command(f'STREAM FILE {subopcion_1_2} ""')
                else:
                    if opcion_invalida:
                        self.send_command(f'STREAM FILE {opcion_invalida} ""')

            elif digit == "2":
                if opcion2:
                    self.send_command(f'STREAM FILE {opcion2} ""')

                lines = self.send_command("WAIT FOR DIGIT 5000")
                digit_code = self.get_result_value(lines)
                digit_sub = chr(int(digit_code)) if digit_code and digit_code.isdigit() else None

                if digit_sub == "1" and subopcion_2_1:
                    self.send_command(f'STREAM FILE {subopcion_2_1} ""')
                elif digit_sub == "2" and subopcion_2_2:
                    self.send_command(f'STREAM FILE {subopcion_2_2} ""')
                else:
                    if opcion_invalida:
                        self.send_command(f'STREAM FILE {opcion_invalida} ""')

            elif digit == "3":
                if opcion3:
                    self.send_command(f'STREAM FILE {opcion3} ""')

            elif digit == "4":
                if opcion4:
                    self.send_command(f'STREAM FILE {opcion4} ""')

            else:
                if opcion_invalida:
                    self.send_command(f'STREAM FILE {opcion_invalida} ""')

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


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    server = ThreadedTCPServer(("192.168.2.10", 4573), FastAGIHandler)
    print("Servidor FastAGI corriendo en puerto 4573 (multicliente)...")
    server.serve_forever()
'''


