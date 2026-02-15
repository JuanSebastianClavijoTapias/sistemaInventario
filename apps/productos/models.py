from django.db import models

from apps.proveedores.models import Proveedores

# Create your models here.
class Productos(models.Model):
    idProducto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField()
    proveedor = models.ForeignKey(
        Proveedores,
        on_delete= models.CASCADE,
        related_name="productos"
    )
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock}"
    
