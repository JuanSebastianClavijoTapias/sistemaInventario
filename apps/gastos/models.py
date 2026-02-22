from django.db import models
from django.utils import timezone

from apps.proveedores.models import Proveedores

# Create your models here.
class Gastos(models.Model):
    CATEGORIA_CHOICES = [
        ('administracion', 'Administración de la Empresa'),
        ('trabajadores', 'Trabajadores'),
        ('comercio_productos', 'Comercio y Productos'),
        ('otros', 'Otros'),
    ]
    
    idGasto = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=20, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='otros'
    )
    proveedor = models.ForeignKey(
        Proveedores,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"
    
    class Meta:
        ordering = ['-fecha']
