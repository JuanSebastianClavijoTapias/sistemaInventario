from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json


class RegistroAuditoria(models.Model):
    """
    Modelo para registrar todas las acciones (auditoría) realizadas en el sistema.
    Captura información de qué, quién, cuándo y cambios antes/después.
    """
    
    ACCIONES = [
        ('crear', 'Creación'),
        ('editar', 'Edición'),
        ('eliminar', 'Eliminación'),
        ('pagar', 'Pago/Abono'),
        ('saldar', 'Saldar Deuda'),
        ('cambio_estado', 'Cambio de Estado'),
    ]
    
    MODELOS_REGISTRADOS = {
        'cliente': 'Clientes',
        'proveedor': 'Proveedores',
        'producto': 'Productos',
        'venta': 'Ventas',
        'gasto': 'Gastos',
        'pago': 'Pagos',
    }

    # Información de la acción
    accion = models.CharField(
        max_length=20,
        choices=ACCIONES,
        help_text="Tipo de acción realizada"
    )
    
    # Usuario que realizó la acción
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='registros_auditoria',
        help_text="Usuario que realizó la acción"
    )
    
    # Información del modelo/entidad afectada
    tipo_contenido = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        help_text="Tipo de modelo afectado"
    )
    id_objeto = models.PositiveIntegerField(
        help_text="ID del objeto afectado"
    )
    modelo = models.CharField(
        max_length=50,
        help_text="Nombre del modelo para referencia rápida"
    )
    descripcion_objeto = models.CharField(
        max_length=255,
        help_text="Descripción legible del objeto (ej: nombre del cliente)"
    )
    
    # Cambios realizados
    valores_antes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Valores del objeto antes del cambio"
    )
    valores_despues = models.JSONField(
        default=dict,
        blank=True,
        help_text="Valores del objeto después del cambio"
    )
    campos_modificados = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de campos que fueron modificados"
    )
    
    # Información adicional
    detalles = models.TextField(
        blank=True,
        help_text="Detalles adicionales de la acción (ej: motivo de pago, monto)"
    )
    
    # Timestamp
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de la acción"
    )
    
    # IP del cliente (opcional)
    ip_cliente = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP del cliente que realizó la acción"
    )
    
    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        indexes = [
            models.Index(fields=['-fecha_hora']),
            models.Index(fields=['usuario', '-fecha_hora']),
            models.Index(fields=['modelo', '-fecha_hora']),
            models.Index(fields=['accion', '-fecha_hora']),
        ]

    def __str__(self):
        return f"{self.get_accion_display()} - {self.descripcion_objeto} ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"

    def obtener_cambios_legibles(self):
        """
        Retorna un diccionario con los cambios legibles para mostrar en templates.
        """
        cambios = {}
        for campo in self.campos_modificados:
            valor_antes = self.valores_antes.get(campo, 'N/A')
            valor_despues = self.valores_despues.get(campo, 'N/A')
            cambios[campo] = {
                'antes': valor_antes,
                'despues': valor_despues
            }
        return cambios

    def obtener_resumen(self):
        """
        Retorna un resumen legible y amigable de la acción para mostrar en el dashboard.
        Usa segunda persona ("Registraste", "Saldaste") e información enriquecida.
        """
        import json
        
        # Intentar parsear detalles como JSON
        detalles_dict = {}
        if self.detalles:
            try:
                detalles_dict = json.loads(self.detalles) if isinstance(self.detalles, str) else self.detalles
            except:
                pass
        
        # Generar mensajes amigables por tipo de acción
        if self.accion == 'crear':
            if self.modelo == 'venta':
                cliente = detalles_dict.get('cliente_nombre', self.descripcion_objeto)
                return f"Registraste una venta a {cliente}"
            elif self.modelo == 'cliente':
                return f"Registraste un nuevo cliente: {self.descripcion_objeto}"
            elif self.modelo == 'proveedor':
                return f"Registraste un nuevo proveedor: {self.descripcion_objeto}"
            elif self.modelo == 'producto':
                return f"Registraste un nuevo producto: {self.descripcion_objeto}"
            elif self.modelo == 'gasto':
                return f"Registraste un gasto: {self.descripcion_objeto}"
            else:
                return f"Registraste: {self.descripcion_objeto}"
        
        elif self.accion == 'editar':
            if self.modelo == 'venta':
                return f"Actualizaste una venta: {self.descripcion_objeto}"
            elif self.modelo == 'cliente':
                return f"Actualizaste datos de {self.descripcion_objeto}"
            elif self.modelo == 'proveedor':
                return f"Actualizaste datos de {self.descripcion_objeto}"
            elif self.modelo == 'producto':
                return f"Actualizaste datos del producto {self.descripcion_objeto}"
            else:
                campos = len(self.campos_modificados) if self.campos_modificados else 1
                return f"Actualizaste {campos} campo(s) en {self.descripcion_objeto}"
        
        elif self.accion == 'eliminar':
            if self.modelo == 'venta':
                return f"Eliminaste una venta de {detalles_dict.get('cliente_nombre', 'un cliente')}"
            elif self.modelo == 'cliente':
                return f"Eliminaste al cliente: {self.descripcion_objeto}"
            elif self.modelo == 'proveedor':
                return f"Eliminaste al proveedor: {self.descripcion_objeto}"
            elif self.modelo == 'producto':
                return f"Eliminaste el producto: {self.descripcion_objeto}"
            else:
                return f"Eliminaste: {self.descripcion_objeto}"
        
        elif self.accion == 'pagar':
            if self.modelo == 'venta':
                cliente = detalles_dict.get('cliente_nombre', 'un cliente')
                monto = detalles_dict.get('monto', '')
                return f"Saldaste una venta con: {cliente} {f'(${monto})' if monto else ''}"
            else:
                monto = detalles_dict.get('monto', '')
                return f"Registraste un pago {f'de ${monto}' if monto else ''} en {self.descripcion_objeto}"
        
        elif self.accion == 'saldar':
            if self.modelo == 'proveedor':
                proveedor = detalles_dict.get('proveedor_nombre', self.descripcion_objeto)
                return f"Saldaste con tu proveedor: {proveedor}"
            else:
                return f"Saldaste deuda de {self.descripcion_objeto}"
        
        elif self.accion == 'cambio_estado':
            estado = detalles_dict.get('nuevo_estado', 'desconocido')
            return f"Cambiaste estado de {self.descripcion_objeto} a {estado}"
        
        else:
            return f"Realizaste: {self.descripcion_objeto}"


class ConfiguracionAuditoria(models.Model):
    """
    Modelo para configuración del sistema de auditoría.
    Permite activar/desactivar auditoría para ciertos modelos.
    """
    MODELOS_DISPONIBLES = [
        ('Clientes', 'Clientes'),
        ('Proveedores', 'Proveedores'),
        ('Productos', 'Productos'),
        ('Ventas', 'Ventas'),
        ('Gastos', 'Gastos'),
    ]
    
    modelo = models.CharField(
        max_length=50,
        unique=True,
        choices=MODELOS_DISPONIBLES
    )
    auditar_creacion = models.BooleanField(default=True)
    auditar_edicion = models.BooleanField(default=True)
    auditar_eliminacion = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Configuración de Auditoría'
        verbose_name_plural = 'Configuraciones de Auditoría'
    
    def __str__(self):
        return f"Auditoría: {self.modelo}"
