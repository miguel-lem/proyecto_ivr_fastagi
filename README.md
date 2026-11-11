# Proyecto IVR con FastAGI, Asterisk y Django

Sistema de IVR (respuesta de voz interactiva) que integra **Asterisk** (vía FastAGI y AMI), una API en **Django**, una base de datos **PostgreSQL** y tareas asíncronas con **Celery + RabbitMQ**. Registra las interacciones de las llamadas (teclas presionadas, pasos a extensión y estados de llamada) en la base de datos.

## Estructura del proyecto

```
.
├── 04_pruebasTiemposaudio/   # Proyecto Django (API, modelos, migraciones)
│   ├── proyectdjango/        # Configuración (settings.py, urls.py, ...)
│   └── carpeta_llamadas/     # App con modelos y vistas de llamadas
├── scripts/                  # Servidores FastAGI y servidores socket hacia la DB
│   ├── principal.py          # Lanza todos los scripts a la vez
│   ├── conAgi.py             # Servidor FastAGI (puerto 4573)
│   ├── conAgiestados.py      # Servidor FastAGI de estados (puerto 4574)
│   ├── registrar_tecla.py    # Servidor socket -> guarda interacciones (puerto 6000)
│   ├── registrar_estados.py  # Servidor socket -> guarda estados (puerto 6010)
│   └── indicaciones_proyecto.txt
└── celery/                   # Tareas asíncronas (Fase 2)
    ├── tareas.py
    └── ejecuCelery.py
```

## ⚠️ Importante: configuración de conexiones (IPs y credenciales de ejemplo)

Los valores de conexión que aparecen en el código **corresponden a una máquina virtual de prueba** usada durante el desarrollo. **No funcionarán en tu equipo tal cual**: debes cambiarlos según tu propio entorno (tu PC, tu servidor, tu VM o tu contenedor).

Ejemplo, en [scripts/registrar_tecla.py](scripts/registrar_tecla.py):

```python
conn = psycopg2.connect(
    host="192.168.2.18",       # IP de la VM de prueba -> cámbiala por la de tu servidor de DB
    port=5432,                 # Puerto de PostgreSQL
    dbname="ivruno",           # Nombre de tu base de datos
    user="postgres",           # Tu usuario de PostgreSQL
    password="mi_contrasena"   # Tu contraseña (¡no uses esta!)
)
```

Ajusta los valores así:

| Parámetro | Qué poner |
|-----------|-----------|
| `host` | IP o nombre del equipo donde corre PostgreSQL. Usa `localhost` si la DB está en tu misma PC. |
| `port` | Puerto de PostgreSQL (por defecto `5432`). |
| `dbname` | Nombre de la base de datos que creaste. |
| `user` / `password` | Credenciales de tu PostgreSQL. |

### Configuración de Django (`settings.py`)

Lo mismo aplica para la base de datos de Django, en [04_pruebasTiemposaudio/proyectdjango/settings.py](04_pruebasTiemposaudio/proyectdjango/settings.py). Estos datos son de la **VM de prueba** y deben **personalizarse al instalar el proyecto** según tu propio entorno:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ivruno',             # Nombre de tu base de datos
        'USER': 'postgres',           # Tu usuario de PostgreSQL
        'PASSWORD': 'mi_contrasena',  # Tu contraseña (¡no uses esta!)
        'HOST': '192.168.2.18',       # IP de la VM de prueba -> cambia por la de tu servidor (o 'localhost')
        'PORT': '5432'                # Puerto de PostgreSQL
    }
}
```

Los valores de `settings.py` deben coincidir con los usados en los scripts (`registrar_tecla.py`, `registrar_estados.py`), de modo que Django y los scripts apunten a la **misma base de datos**. Si no, las tablas creadas con `python manage.py migrate` no existirán donde los scripts intentan guardar los datos.

### Todos los lugares donde hay que cambiar la configuración

| Archivo | Qué es | Valor de prueba actual |
|---------|--------|------------------------|
| `scripts/registrar_tecla.py` (2 conexiones) | Conexión a PostgreSQL | `192.168.2.18:5432` |
| `scripts/registrar_estados.py` | Conexión a PostgreSQL | `192.168.2.18:5432` |
| `04_pruebasTiemposaudio/proyectdjango/settings.py` (`DATABASES`) | Conexión de Django a PostgreSQL | `192.168.2.18:5432` |
| `04_pruebasTiemposaudio/carpeta_llamadas/views.py` | IP de Asterisk (AMI y SSH), usuario/clave AMI | `192.168.2.18`, `admin` |
| `scripts/conAgi.py` y `scripts/conAgiestados.py` | IP donde escucha el servidor FastAGI | `192.168.2.10` (puertos 4573 / 4574) |
| `celery/tareas.py` | Broker RabbitMQ | `amqp://guest:guest@192.168.2.18:5672//` |

> **Recomendación de seguridad:** no dejes contraseñas escritas en el código ni las subas a un repositorio público. Lo ideal es leerlas desde variables de entorno o un archivo `.env`, por ejemplo:
>
> ```python
> import os
> conn = psycopg2.connect(
>     host=os.getenv("DB_HOST", "localhost"),
>     port=int(os.getenv("DB_PORT", 5432)),
>     dbname=os.getenv("DB_NAME", "ivruno"),
>     user=os.getenv("DB_USER", "postgres"),
>     password=os.getenv("DB_PASSWORD"),
> )
> ```

## Requisitos previos

Se recomienda tener conocimientos de Asterisk, Python, Django, sockets, hilos, AMI y el uso de un cliente REST (Postman u otro).

- Python 3.10+
- Asterisk (con un usuario AMI configurado)
- PostgreSQL (en contenedor, VM o local)
- RabbitMQ (para la Fase 2, con Celery)
- Un softphone para probar las extensiones
- Un cliente REST (Postman, etc.)

## Puesta en marcha

1. Crear y activar un entorno virtual.
2. Instalar las dependencias (revisa los `import` de cada archivo: `django`, `psycopg2`, `celery`, `requests`, `paramiko`, etc.).
3. Configurar en Asterisk un usuario AMI.
4. Configurar `extensions.conf` y `pjsip.conf` en Asterisk (ver `scripts/Instrucciones_asterisk.txt`).
5. Dar permisos en Asterisk a las rutas necesarias para el usuario (usa el usuario con el que ingresas a Linux, no `root`).
6. Instalar y configurar PostgreSQL, crear la base de datos y **ajustar las conexiones** según la sección anterior.
7. Aplicar las migraciones de Django:
   ```bash
   cd 04_pruebasTiemposaudio
   python manage.py migrate
   python manage.py runserver
   ```
8. Iniciar los scripts desde la carpeta `scripts` (el principal lanza a los demás):
   ```bash
   cd scripts
   python principal.py
   ```
9. Enviar la solicitud de llamada con un cliente REST a la API de Django.

## Ejemplo: realizar una llamada desde Postman (u otro cliente REST)

Endpoint (Django en local, puerto 8000 por defecto):

```
POST http://localhost:8000/api/llamadas/realizar_llamadaunica/
Content-Type: application/json
```

Body (raw → JSON):

```json
{
    "channel": "SIP/100",
    "exten": "100",
    "context": "default",
    "priority": 1,
    "callerid": "Mi llamada",
    "numero_celular": "0911111111"
}
```

> ⚠️ Estos valores son **solo de ejemplo**. Cámbialos según tu entorno.
>
> En `numero_celular` coloca el número al cual llamas. No escribas comentarios (`#`) dentro del JSON, porque Postman lo rechazaría como JSON inválido.

| Campo | Descripción |
|-------|-------------|
| `channel` | Canal de Asterisk, por ejemplo `SIP/100`. La API lo convierte internamente en `Local/<channel>@default`. |
| `exten` | Extensión/destino en el dialplan de Asterisk (`extensions.conf`) al que entra la llamada. |
| `context` | Contexto del dialplan donde está esa extensión (en el ejemplo, `default`). |
| `priority` | Prioridad dentro de la extensión (normalmente `1`). |
| `callerid` | Texto o número que se mostrará como identificador de la llamada. |
| `numero_celular` | Número al cual llamas (el cliente); se usa para consultar sus datos en la DB y generar los audios personalizados. Si el usuario no existe, la llamada no se ejecuta. |

Con `curl`:

```bash
curl -X POST http://localhost:8000/api/llamadas/realizar_llamadaunica/ \
  -H "Content-Type: application/json" \
  -d '{"channel":"SIP/100","exten":"100","context":"default","priority":1,"callerid":"Mi llamada","numero_celular":"0911111111"}'
```

Respuestas:
- `200`: la llamada fue originada correctamente.
- `400`: error al realizar la llamada.
- Mensaje `La llamada no se puede ejecutar, no existe el usuario`: el `numero_celular` no está registrado en la DB.

La URL `http://localhost:8000/...` también está escrita en `celery/tareas.py`; cámbiala si Django corre en otra máquina o puerto.

### Fase 2 – Celery

La tarea `enviar_datos(channel, exten)` de `celery/tareas.py` envía automáticamente ese mismo payload (con `context: "default"`, `priority: 1` y `callerid: "Mi llamada"` fijos, y `numero_celular` igual a `channel`, por lo que ahí `channel` debe recibir el número al que se llama) al endpoint anterior.


1. Instalar RabbitMQ en un contenedor (actúa como broker de Celery).
2. Ajustar la URL del broker en `celery/tareas.py`.
3. Ejecutar el worker de Celery (ver `celery/ejecuCelery.py`).

## Flujo general

1. Un cliente REST solicita una llamada a la API de Django.
2. Django usa AMI para originar la llamada en Asterisk.
3. Asterisk ejecuta el IVR mediante FastAGI (`conAgi.py` / `conAgiestados.py`).
4. Cada interacción se envía por socket a `registrar_tecla.py` / `registrar_estados.py`.
5. Estos scripts guardan los datos en PostgreSQL.
