# archivo: principal.py
#este script es para poder ejecutar un grupo de scripts al unisono y no estar abriendo una consola por cada uno 
import subprocess

# Ejecuta el servidor de base de datos (registrar_tecla.py)
socket_server = subprocess.Popen(["python", "registrar_tecla.py"])

# Ejecuta el servidor de base de datos (registrar_estados.py)
socket_server2 = subprocess.Popen(["python", "registrar_estados.py"])

# Ejecuta el servidor FastAGI (conAgi.py)
fastagi_server = subprocess.Popen(["python", "conAgi.py"])

# Ejecuta el servidor FastAGI para guardar estados (conAgiestados.py)
fastagi_server2 = subprocess.Popen(["python", "conAgiestados.py"])

# Espera a que los procesos terminen (opcional)
socket_server.wait()
socket_server2.wait()
fastagi_server.wait()
fastagi_server2.wait()
