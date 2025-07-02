from rest_framework import routers
from django.urls import path
from carpeta_llamadas.views import LlamadasView3
from rest_framework.urlpatterns import format_suffix_patterns


router = routers.DefaultRouter() 

#ruta para la navegacion
router.register(r'llamada',LlamadasView3, basename = 'carpeta_llamadas')

# Agrega manualmente la acción personalizada
urlpatterns = [
    path('realizar_llamadaunica/', LlamadasView3.as_view({'post': 'realizar_llamadaunica'}), name='realizar_llamadaunica'),
]


urlpatterns += router.urls

# Si necesitas soporte para los sufijos de formato (json, xml, etc.)
urlpatterns = format_suffix_patterns(urlpatterns)