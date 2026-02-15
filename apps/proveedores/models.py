from django.db import models

# Create your models here.

class Proveedores(models.Model):
    idProveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=100)
    inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return self.nombre
    
