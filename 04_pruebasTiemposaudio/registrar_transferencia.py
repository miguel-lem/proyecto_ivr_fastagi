# registrar_transferencia.py
import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tu_proyecto.settings")
django.setup()

from carpeta_llamadas.models import Paso_extension

def main():
    if len(sys.argv) < 3:
        print("Uso: registrar_transferencia.py <numero> <extension>")
        return

    numero = sys.argv[1]
    extension = sys.argv[2]

    Paso_extension.objects.create(numero=numero, extension=extension)
    print("Transferencia registrada")

if __name__ == "__main__":
    main()
