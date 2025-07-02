import os
import django
import sys

# Preparar entorno Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyectdjango.settings")
django.setup()

# Ahora sí podés importar tus modelos
from carpeta_llamadas.models import Interac_llamadas  # <-- Ajustá 'app' al nombre real de tu aplicación

import sys

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: registrar_tecla.py <numero> <opcion>")
        sys.exit(1)

    numero = sys.argv[1]
    opcion = sys.argv[2]

    # Guardar en la base de datos
    Interac_llamadas.objects.create(numero=numero, opcion=opcion)
    print(f"Guardado: {numero} presionó la opción {opcion}")
