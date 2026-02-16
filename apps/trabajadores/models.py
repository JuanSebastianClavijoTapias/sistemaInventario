from django.db import models
from django.utils import timezone

# Create your models here.
class Trabajadores(models.Model):
    CARGO_CHOICES = [
        ('gerente', 'Gerente'),
        ('vendedor', 'Vendedor'),
        ('cajero', 'Cajero'),
        ('almacenista', 'Almacenista'),
        ('repartidor', 'Repartidor'),
        ('limpieza', 'Personal de Limpieza'),
        ('otro', 'Otro'),
    ]

    idTrabajador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    telefono = models.CharField(max_length=22)
    cargo = models.CharField(
        max_length=20,
        choices=CARGO_CHOICES,
        default='otro'
    )
    salario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_ingreso = models.DateField(default=timezone.now)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_cargo_display()}"
