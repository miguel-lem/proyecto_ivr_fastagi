# archivo: principal.py
import subprocess

# Ejecuta el servidor de base de datos (registrar_tecla.py)
socket_server = subprocess.Popen(["python", "registrar_tecla.py"])

# Ejecuta el servidor FastAGI (conAgi.py)
fastagi_server = subprocess.Popen(["python", "conAgi.py"])

# Espera a que ambos procesos terminen (opcional)
socket_server.wait()
fastagi_server.wait()
