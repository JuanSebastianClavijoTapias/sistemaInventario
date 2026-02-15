from django.db import models

from apps.clientes.models import Clientes
from apps.productos.models import Productos

# Create your models here.

class Venta(models.Model):
    idVenta = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Clientes,
        on_delete= models.CASCADE,
        related_name="ventas"
    )
    producto = models.ForeignKey(
        Productos,
        on_delete= models.CASCADE
    )
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Venta: {self.idVenta} - Cliente: {self.cliente.nombre}"
    

