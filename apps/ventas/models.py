from django.db import models
from django.utils import timezone
from datetime import timedelta

from apps.clientes.models import Clientes
from apps.productos.models import Productos

# Create your models here.

class Venta(models.Model):
    TIPO_PAGO_CHOICES = [
        ('completo', 'Pago Completo'),
        ('fiado', 'Pago a Crédito'),
    ]
    
    ESTADO_PAGO_CHOICES = [
        ('pagado', 'Pagado'),
        ('pendiente', 'Pendiente'),
        ('vencido', 'Vencido'),
    ]
    
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
    
    # Nuevos campos para pagos a crédito
    tipo_pago = models.CharField(
        max_length=10,
        choices=TIPO_PAGO_CHOICES,
        default='completo'
    )
    monto_pagado = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True
    )
    estado_pago = models.CharField(
        max_length=10,
        choices=ESTADO_PAGO_CHOICES,
        default='pagado'
    )
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de pago"""
        return self.total - self.monto_pagado
    
    @property
    def dias_para_vencimiento(self):
        """Calcula los días restantes para el vencimiento"""
        if self.fecha_vencimiento and self.estado_pago == 'pendiente':
            return (self.fecha_vencimiento - timezone.now().date()).days
        return None
    
    @property
    def esta_vencido(self):
        """Verifica si la venta está vencida"""
        return self.estado_pago == 'vencido' or (
            self.fecha_vencimiento and 
            self.fecha_vencimiento < timezone.now().date() and 
            self.estado_pago == 'pendiente'
        )
    
    def actualizar_estado_pago(self):
        """Actualiza el estado de pago basado en la fecha actual"""
        if self.tipo_pago == 'completo':
            self.estado_pago = 'pagado'
        elif self.monto_pagado >= self.total:
            self.estado_pago = 'pagado'
        elif self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date():
            self.estado_pago = 'vencido'
        else:
            self.estado_pago = 'pendiente'
        self.save()
    
    def __str__(self):
        return f"Venta: {self.idVenta} - Cliente: {self.cliente.nombre}"
    

