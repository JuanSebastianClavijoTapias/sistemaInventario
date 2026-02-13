from django.apps import AppConfig
from . import apps

class ClientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clientes'
