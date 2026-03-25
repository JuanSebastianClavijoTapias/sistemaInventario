from django.db import models
from django.utils import timezone
from datetime import timedelta

from apps.clientes.models import Clientes
from apps.productos.models import Productos

# Create your models here.

METODO_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('tarjeta', 'Tarjeta'),
]

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
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campos de precios y ganancia
    precio_compra = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name="Precio de Compra (unitario)"
    )
    precio_venta = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name="Precio de Venta (unitario)"
    )
    ganancia = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name="Ganancia Total"
    )
    
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
    metodo_pago = models.CharField(
        max_length=10,
        choices=METODO_PAGO_CHOICES,
        default='efectivo',
        verbose_name="Método de Pago"
    )
    
    @property
    def descripcion(self):
        """Returns product description for display"""
        if self.pk:
            detalles = list(self.detalles.all())
            if detalles:
                items = [f"{d.cantidad} {d.producto.nombre}" for d in detalles]
                return ", ".join(items)
        if self.producto:
            return self.producto.nombre
        return "Sin producto"
    
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
        """Verifica si la fecha de pago sugerida ya pasó"""
        return (
            self.fecha_vencimiento and 
            self.fecha_vencimiento < timezone.now().date() and 
            self.estado_pago == 'pendiente'
        )
    
    def actualizar_estado_pago(self):
        """Actualiza el estado de pago"""
        if self.tipo_pago == 'completo':
            self.estado_pago = 'pagado'
        elif self.monto_pagado >= self.total:
            self.estado_pago = 'pagado'
        else:
            self.estado_pago = 'pendiente'
        self.save()
    
    def __str__(self):
        return f"Venta: {self.idVenta} - Cliente: {self.cliente.nombre}"


class Cobro(models.Model):
    """Registra cada pago/cobro realizado sobre una venta a crédito"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='cobros')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Cobro ${self.monto} - Venta #{self.venta.idVenta}"


class DetalleVenta(models.Model):
    """Detalle de cada producto en una venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ganancia = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad} - Venta #{self.venta.idVenta}"

