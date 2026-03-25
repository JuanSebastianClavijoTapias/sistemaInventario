from django.db import models

from apps.proveedores.models import Proveedores

CATEGORIA_CHOICES = [
    ('papa_primera', 'Papa Primera'),
    ('tronco', 'Tronco'),
    ('medio_pollo', 'Medio Pollo'),
    ('pelona', 'Pelona'),
    ('rechazo_grueso', 'Rechazo Grueso'),
    ('rechazo_medio', 'Rechazo Medio'),
    ('tercera', 'Tercera'),
    ('sobrante', 'Sobrante'),
    ('otros', 'Otros'),
]

# Create your models here.
class Productos(models.Model):
    idProducto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='otros', verbose_name="Categoría")
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Precio de Compra")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Precio de Venta")
    stock = models.IntegerField()
    proveedor = models.ForeignKey(
        Proveedores,
        on_delete= models.CASCADE,
        related_name="productos"
    )
    
    @property
    def ganancia_unitaria(self):
        """Calcula la ganancia por unidad"""
        return self.precio_venta - self.precio_compra
    
    @property
    def margen_ganancia(self):
        """Calcula el porcentaje de margen de ganancia"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock}"
    
