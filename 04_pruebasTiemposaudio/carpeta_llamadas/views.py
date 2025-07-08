from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .models import Cliente, Mensajes, Promociones

# views.py
import time
from django.http import JsonResponse
from rest_framework import viewsets
from pystrix import ami
import socket
import json
from rest_framework.viewsets import ViewSet
import pyttsx3
from django.http import FileResponse, JsonResponse
import os
import subprocess
import uuid
from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
import datetime

# Variables que se utilizaran para la configuracion y enlace con AMI
_HOST = '192.168.2.18'
_USERNAME = 'admin'
_PASSWORD = 'mi_contrasenia'

#esta clase es para realziar la llamada a una sola extension, esta parte esta 
#para realziar pruebas de conjugacion entre ami y agi
#la primera es para que se ejecute la llamada y la segunda es para que tome las acciones de teclas
class RealizarLllamada:
    """
    Clase para manejar la lógica de la sesión AMI.
    """
    _manager = None
    _kill_flag = False 

    def __init__(self):
        self._manager = ami.Manager()
        try:
            self._manager.connect(_HOST)

            # Solicitar el token de desafío para la autenticación
            challenge_response = self._manager.send_action(ami.core.Challenge())
            if challenge_response and challenge_response.success:
                action = ami.core.Login(_USERNAME, _PASSWORD, challenge=challenge_response.result['Challenge'])
                self._manager.send_action(action)
            else:
                self._kill_flag = True
                raise ConnectionError("Asterisk no proporcionó el token MD5 de desafío")

        except ami.ManagerSocketError as e:
            self._kill_flag = True
            raise ConnectionError(f"No se puede conectar al servidor Asterisk: {str(e)}")
        except ami.core.ManagerAuthError as reason:
            self._kill_flag = True
            raise ConnectionError(f"No se puede autenticar en el servidor Asterisk: {reason}")
        except ami.ManagerError as reason:
            self._kill_flag = True
            raise ConnectionError(f"Ocurrió un error inesperado en Asterisk: {reason}")

        self._manager.monitor_connection()

    def kill(self):
        self._manager.close()

    def is_alive(self):
        return not self._kill_flag

    #funcion para realziar la llamada
    def realizar_llamada(self, channel, exten,context, priority, callerid,lista_audios):
        # Crear la acción de origen para realizar una llamada 
        action = ami.core._Originate(
            channel=channel,
            timeout=30000,
            callerid=callerid,
            variables={
                'AUDIOS': '|'.join(lista_audios)
            },
        )
        #impresion para probar que pasen todos los nombres dentro del vector
        print("ESTA ES LA LISTA DE AUDIOS QUE SE ESTA PASANDO:-----------------------")
        print(lista_audios)
        # Establecer el contexto y la extensión (esto puede necesitar ajustes dependiendo de tu implementación)
        action['Context'] = context#este conexto es el que se agrego dentro de extensions
        action['Exten'] = exten
        action['Priority'] = priority
        response = self._manager.send_action(action)
        # Verificar respuesta completa (para depuración)
        print(response)

        # Ahora, si el audio ha sido reproducido, podemos colgar o continuar con más acciones
        '''if response.success:
            #creo un objeto de la clase donde escucho eventos
            teclas=EscucharEventos()
            #llamo a la funcion de escucha
            teclas.obtener_teclas_asterisk("admin", "mi_contrasenia", "192.168.2.18")'''
        return response


#esta clase es para poder extraer desde el front los datos, por el momento de la practica se esta utilizando 
#un cliente api rest Postman
class LlamadasView3(viewsets.ViewSet):
    """
    Vista para manejar la llamada desde la API.
    """
    def realizar_llamadaunica(self, request):
        # Extraer los parámetros de la solicitud
        channel = request.data.get('channel', '')
        exten = request.data.get('exten', '')
        context = request.data.get('context', '')
        priority = request.data.get('priority', 1)
        callerid = request.data.get('callerid', '')
        numero_celular = request.data.get('numero_celular', '')

        #realizar la consulta en base al cliente, para ello genero un objeto de la clase
        #donde esta la funcion para generar la union de los textos y devolucion de los nombre es audios
        mediador = Mediador_texto_audio()
        lista_audios=mediador.generar_audios_llamada(numero_celular,"comprada")
        #agrego este control en caso no exista el usuario, porque la secuencia colocada
        #debe entregarme los resultados de valores no encontrados asignados como "0"
        if lista_audios == 0:
            #retorno esta respuesta y no ejecuto la llamada
            return JsonResponse({'message': 'La llamada no se puede ejecutar, no existe el usuario'})
        #llamamos a la funcion de crear el audio y enviarlo a al servidor asteris
        #creo el objeto de crearaudio
        gestor_audio = CrearAudio()
        time.sleep(1)
        #llamo a la funcion con la cual elimino de asterisk los audios que tiene mas de 3 minutos alli
        #de esa manera evito utilizar espacion con audios que no son necesarios
        gestor_audio.cleanup_old_audios(minutes=3)
        print("SE A PROCEDIDO A CREAR AUDIO Y ELIMINAR AUDIO")
        print("---------------------------paso de la extraccion de nombre---------------")
        # Iniciar la conexión AMI que esta en la clas donde creamos la funcion para realziar la llamada
        ami_core = RealizarLllamada()
        # Realizar la llamada, le pasamos los parametros
        response = ami_core.realizar_llamada(channel, exten, context, priority, callerid,lista_audios)
        ###return JsonResponse({'message': 'La funcion de llamada esta funcionando bien',
        ###                     'consulta_generada':lista_audios})
        if response.success:
            return JsonResponse({'message': 'La llamada fue exitosa'})
        else:
            return JsonResponse({'message': 'Hubo un error al realizar la llamada'}, status=400)


#esta clase es para poder generar el audio, esta con ViewSet porque las primeras pruebas fueron realizadas
#con cliente rest, pero se cambio 
#los cambios agregados permiten que se cree el audio a travez d un texto, se convierta a formato de asterisk
#y luego se lo pueda subir al servidor, 
#tambien se agrego la funcionalidad de que elimine el archivo en el servidor si ya tiene mas de tres minutos alli
class CrearAudio(ViewSet):
    def __init__(self):
        # Configuración del servidor Asterisk remoto
        #aqui se agrego la coneccion ssh para poder tener acceso al servidor de asterisk 
        #de esa manera almacenar y poder aliminar archivos de audio de la ruta de sonidos de asterisk
        self.asterisk_server = {
            'hostname': '192.168.2.18',  # ip de donde esta instalado asterisk, en este caso una VM
            'port': 22,  # Puerto SSH
            'username': 'pcprueba',#este usuario dee ser el que tiene accedo con permisos a la carpeta de sonidos
            'password': '12345',#la contraseña es configurable en caso de crear un usuario
            'remote_path': '/var/lib/asterisk/sounds/'  # Ruta donde se guardarán los audios
        }


    #funcion para convertir el texto en audio
    def text_to_speech(self,texto):
        #aqui creo la variable con el texto que quiero convertir, 
        #por el momento cuando creo esta parte es asi, ya luego se agregara con consultas hacia la base de datos
        #debido a que cada llamada debera ser personalizada
        ###texto="Estimado cliente Evelin Sandoval, en representacion de Banco del Pacífico, el ESTUDIO JURIDICO ROMERO D Y ASOCIADOS le recuerda que mantiene su credito vencido con un saldo de $1080"
        ###"""Función para convertir texto a audio en formato compatible con Asterisk"""
        if not texto:
            #aqui se lo pued modificar y en caso no proporcionen texto, para pasarle alguno por defecto
            raise ValueError("No se proporcionó texto")

        try:
            #aqui estan los pasos para administrar el proceso de generar el audio y de eliminacion temporal
            # 1. Generar audio inicial con pyttsx3
            output_file = self._generate_tts_audio(texto)
            if not output_file:
                raise RuntimeError("Error al generar el audio")

            # 2. Convertir a formato compatible con Asterisk
            converted_file = self._convert_to_asterisk_format(output_file)
            
            # 3. Limpiar archivo temporal original
            if os.path.exists(output_file):
                os.remove(output_file)

            if not converted_file:
                raise RuntimeError("Error al convertir el audio")

            # 4. Enviar el archivo al servidor Asterisk
            #aqui le capturo el nombre con el cual se esta guardando en el servidor de asterisk
            remote_filename = self._send_to_asterisk_server(converted_file)

            # 5. Limpiar archivo local convertido
            if os.path.exists(converted_file):
                os.remove(converted_file)

            #le retorno el nombre capturado, porque es la variable que envio a la funcion de geenrar la llamada
            return remote_filename

        except Exception as e:
            # Limpieza en caso de error
            if 'output_file' in locals() and os.path.exists(output_file):
                os.remove(output_file)
            if 'converted_file' in locals() and converted_file and os.path.exists(converted_file):
                os.remove(converted_file)
            raise e

    #funcion para enviar el archivo a asterisk
    def _send_to_asterisk_server(self, local_file):
        """Envía el archivo al servidor Asterisk remoto via SFTP"""
        #inicio la coneccion a ssh
        ssh = SSHClient()
        # Configuracion de política para auto-agregar claves desconocidas, 
        #se esta utilizando por las pruebas, luego ya se debe quitar cuando salga a produccion
        #y buscar alguna alternativa
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        
        try:
            # Conectar al servidor remoto
            ssh.connect(
                hostname=self.asterisk_server['hostname'],
                port=self.asterisk_server['port'],
                username=self.asterisk_server['username'],
                password=self.asterisk_server['password'],
                timeout=10  # Tiempo fuera para evitar bloqueos
            )
            
            #Verificar permisos del directorio remoto
            sftp = ssh.open_sftp()

            try:
                sftp.chdir(self.asterisk_server['remote_path'])
            except IOError:
                raise RuntimeError(f"El directorio remoto no existe o no es accesible: {self.asterisk_server['remote_path']}")
                
            #Subir archivo con permisos explícitos (para este determinado formato)
            remote_filename = f"converted_temp_audio_{uuid.uuid4().hex}.wav"
            #controlo la ruta donde estoy almacenando el archivo
            remote_path = f"{self.asterisk_server['remote_path']}{remote_filename}"
            
            # Subir el archivo
            sftp.put(local_file, remote_path)
            
            # Asegurarse de que los permisos son correctos
            sftp.chmod(remote_path, 0o644)  # -rw-r--r--
            #Verificar que el archivo se creó correctamente
            try:
                if sftp.stat(remote_path).st_size == 0:
                    sftp.remove(remote_path)
                    raise RuntimeError("El archivo remoto se subió vacío")
            except IOError:
                raise RuntimeError("No se pudo verificar el archivo remoto")
            
            # Retorno el nombre del archivo
            return remote_filename  
            
        except Exception as e:
            # Limpieza en caso de error durante la subida
            if 'remote_path' in locals():
                try:
                    sftp.remove(remote_path)
                except:
                    pass
            raise RuntimeError(f"Error al subir archivo: {str(e)}")
        finally:
            if 'sftp' in locals():
                sftp.close()
            ssh.close()
    
    #funcion para eliminar los archivos viejos dentro de asterisk
    def cleanup_old_audios(self, minutes=3):
        """Elimina archivos de audio más antiguos que X minutos del servidor Asterisk"""
        #genero las conecciones
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        
        try:
            ssh.connect(
                hostname=self.asterisk_server['hostname'],
                port=self.asterisk_server['port'],
                username=self.asterisk_server['username'],
                password=self.asterisk_server['password']
            )
            
            sftp = ssh.open_sftp()
            cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
            
            try:
                #le paso la ruta
                for filename in sftp.listdir(self.asterisk_server['remote_path']):
                    #controlo que elija los audios que empeicen en base al nombre creado y con formato wav
                    #este control esta agregado para evitar eliminar los otros audios que contiene asterisk
                    if filename.startswith('converted_temp_audio_') and filename.endswith('.wav'):
                        filepath = self.asterisk_server['remote_path'] + filename
                        #el try catch es en caso de que no exista algun archivo que empiece con ese nombre
                        try:
                            #consulto el archivo en la ruta, es decir lo extraigo
                            file_attr = sftp.stat(filepath)
                            #coversion de tiempo de cuando fuecreado
                            file_time = datetime.datetime.fromtimestamp(file_attr.st_mtime)
                            #comparo si el tiempo es mas de tres minutos de haber sido creado
                            if file_time < cutoff_time:
                                #lo elimino si cumple con el tiempo
                                sftp.remove(filepath)
                                print(f"Eliminado archivo antiguo: {filename}")
                        except IOError:
                            # Si el archivo ya no existe o hay error al acceder, continuamos
                            continue
            except IOError as e:
                print(f"Error al limpiar archivos: {e}")
                
        except Exception as e:
            print(f"Error en limpieza de audios: {e}")
        finally:
            if 'sftp' in locals():
                sftp.close()
            ssh.close()


    #esta funcion es para eliminar los archivos del sistema desde el cual se esta trabajando 
    def _delete_file(self, file_path):
        """Elimina un archivo si existe"""
        try:
            #buscar si esta en el sistema operativo
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Archivo {file_path} eliminado después del tiempo especificado")
        except Exception as e:
            print(f"Error al eliminar archivo {file_path}: {e}")

    # Funcion para convertir el texto en audio
    def _generate_tts_audio(self, texto):
        """Genera el audio inicial con pyttsx3"""
        try:
            #inicio la funcion
            engine = pyttsx3.init()
            #controplamos la velocidad, el valor mas alto es mas veloz, va hasta 300
            engine.setProperty('rate', 150)
            #control del volumen en el audio rangos que se puede manejar 0.5, 0.8, 1.0
            engine.setProperty('volume', 1.0)

            # Usar nombre de archivo único, con eso evito colision de nombres en el servidor
            output_file = f"temp_audio_{uuid.uuid4().hex}.wav"
            #convierte el audio y lo guarda en la ruta especificada
            engine.save_to_file(texto, output_file)
            #tiene una funcion similar alasyn await, ya que permite terminar un proceso para poder continuar
            engine.runAndWait()

            #retorno el valor y en caso que no se genere regresa un none
            return output_file if os.path.exists(output_file) else None
        except Exception as e:
            print(f"Error en generación TTS: {e}")
            return None

    #funcion para conertir el archivo a un formato compatible con asterisk
    def _convert_to_asterisk_format(self, input_file):
        """Convierte el audio a formato compatible con Asterisk"""
        try:
            # Nombre para archivo convertido
            converted_file = f"converted_{os.path.basename(input_file)}"
            
            # Comando ffmpeg para convertir a formato Asterisk:
            # - 8000Hz (telefonía estándar)
            # - 1 canal (mono)
            # - 16 bits por muestra
            # - Formato WAV PCM
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-ar', '8000',        # Frecuencia de muestreo 8kHz
                '-ac', '1',            # Audio mono
                '-acodec', 'pcm_s16le', # Códec PCM signed 16-bit little-endian
                '-y',                  # Sobrescribir si existe
                converted_file
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            return converted_file if os.path.exists(converted_file) else None
        except subprocess.CalledProcessError as e:
            print(f"Error en ffmpeg: {e.stderr.decode('utf-8')}")
            return None
        except Exception as e:
            print(f"Error en conversión: {e}")
            return None


#clase creada como mediador entre el generador de los textos y el generador de audios
class Mediador_texto_audio():
    @staticmethod
    def generar_audios_llamada(numero_celular: str, cartera: str):
        consulta = Consultas()
        try:
            #Captura de todos los mensajes de acuerdo al grupo
            #Utilizo la funcion que me genera el primer audio personalizado de acuerdo al usuario
            saludo = consulta.generar_saludo_personalizado(numero_celular)  # Audio 0
            print("ANTES DEL PRIMER CONTROL CUANDO NO HAY USUARIO--------------////////-------")
            #genero un control en caso no exista el usuario
            if saludo == 'Error: Cliente no encontrado.':
                #retorno el cero por ser mas facil para utilizar
                return 0
            #creo el texto en base a los mensajes osbrantes de la cartera
            menu_principal = consulta.opcionesdesde1_error(cartera)         # Audios 1–2
            #creo los mensajes en razon de las promociones que se hayan cargado
            promociones = consulta.obtener_todas_promociones()              # Audios 1_1 y 1_2 (repetir),3,4,5
            # se pasa a ordenar los textos de acuerdo a como se trabaje el vector en el fastagi
            #menu_principal contiene exactamente de acuerdo a conveniencia el siguiente orde
            # [[0]saludo(consulta y union),[1]opción1(de_promociones[0]),  
            # [2]opción1_1(de mensajes[0]),[3]opción1_2(de mensajes[1]),
            # [4]opción2(de_promocion[1]), [5]opción2_1(de mensajes[0]),[6]opción2_2(de mensajes[1]),
            # [7]opción3(de mensajes[3]), [8]opción4(de mensajes[4]), [9]error(de mensajes[5])]
            todos_los_mensajes = [saludo]

            # Opción 1
            todos_los_mensajes.append(promociones[0]) # Opcion 1
            todos_los_mensajes.append(menu_principal[0])  # Audio 1_1
            todos_los_mensajes.append(menu_principal[1])  # Audios 1_2
            ###todos_los_mensajes.extend(promociones)        

            # Opción 2
            todos_los_mensajes.append(promociones[1])     # Opcion 2
            todos_los_mensajes.append(menu_principal[0])  # Audio 1_1
            todos_los_mensajes.append(menu_principal[1])  # Audios 1_2
            ###todos_los_mensajes.extend(promociones)     

            # Opción 3
            todos_los_mensajes.append(menu_principal[2])  # Opcion 3

            # Opción 4
            todos_los_mensajes.append(menu_principal[3])  # Opcion 4

            # Opción incorrecta
            todos_los_mensajes.append(menu_principal[4])  # Opcion 5 (error)

            # Creo un objeto del generador de audio para utilizar su funcion
            gestor_audio = CrearAudio()
            #creo un vector vacio para almacenar los nombres y pasarle al ami en la llamada
            nombres_audios = []

            #recorrido del vector para que el generador de audio los convierta de uno en uno
            for texto in todos_los_mensajes:
                #capturo el nombbre que retorna la funcion
                archivo_generado = gestor_audio.text_to_speech(texto)
                #validacion de que el archivo tenga un nombre
                if archivo_generado:
                    #le retiro la extension al nombre porque asterisk puede reconocer automaticamente
                    nombre_audio_sin_ext = Path(archivo_generado).stem.strip()
                    #encolo en el vector que fue creado como vacio
                    nombres_audios.append(nombre_audio_sin_ext)

            #retorno la lista de nombres para que los puedan utilizar
            return nombres_audios
        #atrapado de errores en caso que algo falle
        except Exception as e:
            print(f"Error generando audios IVR: {str(e)}")
            return []


#clase creada para manejar las consultas en un modulo aparte
class Consultas:
    #funcion para extraer los datos de las dos tablar y unirlos
    def generar_saludo_personalizado(self,numero_celular):
        try:
            # Obtener los datos del cliente
            cliente = Cliente.objects.get(numero_celular=numero_celular)
            #control en caso no exista el usuario dentro de la DB
            
            # Buscar el mensaje según el codigo de mensaje
            mensaje_base = Mensajes.objects.get(codigo='saludo-comprada')

            # Reemplazar los campos del mensaje con datos del cliente
            mensaje_final = mensaje_base.mensaje.format(
                nombre_cliente=cliente.nombre,
                banco=cliente.banco,
                monto=cliente.monto
            )
            
            #retornar el texto armado
            return mensaje_final

        except Cliente.DoesNotExist:
            #este retorno es importante porque se lo puede utilizar para continuar o no la llamada
            return "Error: Cliente no encontrado."
        except Mensajes.DoesNotExist:
            return "Error: No se encontró mensaje para esta cartera."
        except Exception as e:
            return f"Error inesperado: {str(e)}"

    #funcion para extraer las demas consultas
    def opcionesdesde1_error(self,cartera):
        try:
            # Excluir el mensaje de saludo
            mensajes = Mensajes.objects.filter(
                tipo_cartera=cartera
            ).exclude(codigo__startswith='saludo-comprada').order_by('id')

            # Retornar la lista de textos
            return [m.mensaje for m in mensajes]

        except Exception as e:
            return [f"Error al obtener mensajes restantes: {str(e)}"]


    def obtener_todas_promociones(self):
        try:
            # 1. Obtener todos los registros ordenados por orden de inserción (por id)
            promociones_queryset = Promociones.objects.all().order_by('id')

            # 2. Extraer solo los mensajes como lista de texto
            mensajes = [promo.mensaje for promo in promociones_queryset]

            # 3. Retornar la lista
            return mensajes

        except Exception as e:
            return [f"Error al obtener promociones: {str(e)}"]

