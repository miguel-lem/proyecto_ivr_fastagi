from django.db import models

#tabla en la cual se guardan los mensjaes que seran la plantilla
class Mensajes(models.Model):
	mensaje = models.TextField(max_length=300)
	tipo_cartera = models.CharField(max_length=100)
	codigo = models.CharField(max_length=200)
	created_at = models.DateTimeField(auto_now_add=True)

#tabla en la cual guardaran los numeros de a quien se debe llamar
class Cliente(models.Model):
	numero_celular = models.CharField(max_length=15, unique=True)
	nombre = models.CharField(max_length=70)
	cartera = models.CharField(max_length=60)
	banco = models.CharField(max_length=80)
	monto = models.CharField(max_length=10)
	###monto = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)


#tabla que contiene la plantilla de promociones
class Promociones(models.Model):
	mensaje = models.TextField(max_length=300)
	codigo = models.CharField(max_length=70)
	created_at = models.DateTimeField(auto_now_add=True)

#tabla en la cual se colocarna los estados de llamadas como: respondio, colgo, buzon, ocupado
class EstadosLlamada(models.Model):
	numero = models.CharField(max_length=20)
	estado = models.CharField(max_length=9)
	created_at = models.DateTimeField(auto_now_add=True)

#tabla en la cual se guardara la interaccion de parte del cliente
class InteraccionLlamada(models.Model):
	numero = models.CharField(max_length=20)
	opcion = models.CharField(max_length=9)
	posicion_vect = models.CharField(max_length=9)
	created_at = models.DateTimeField(auto_now_add=True)

#tabla para guardar la informacion del cliente y si decidio hablar con alguna extension
class PasoExtension(models.Model): 
	numero = models.TextField(max_length=20)
	extension = models.CharField(max_length=10)
	posicion_vect = models.CharField(max_length=9)
	created_at = models.DateTimeField(auto_now_add=True)
