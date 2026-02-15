from django.db import models

from apps.proveedores.models import Proveedores

# Create your models here.
class Gastos(models.Model):
    idGasto =  models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=20,decimal_places=2)
    fecha = models.DateField()
    proveedor = models.ForeignKey(
        Proveedores,
        on_delete= models.SET_NULL,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"
