"""
Utilities para facilitar el registro de auditoría desde las vistas.
"""
from apps.auditoria.models import RegistroAuditoria
from django.contrib.contenttypes.models import ContentType
import json
import logging

logger = logging.getLogger(__name__)


class AuditoriaMixin:
    """
    Mixin para vistas que automatiza la auditoría con datos de la view.
    """
    auditoria_activa = True
    
    def form_valid(self, form):
        """
        Captura el usuario de la request y lo asigna a la instancia.
        """
        if self.auditoria_activa and hasattr(form, 'instance'):
            form.instance._usuario_auditoria = self.request.user
        
        return super().form_valid(form)


class AuditoriaHelper:
    """
    Helper para registrar eventos de auditoría personalizados con información enriquecida.
    """
    
    @staticmethod
    def registrar_saldar_proveedor(proveedor, monto=None, usuario=None):
        """
        Registra cuando se salda deuda con un proveedor.
        Genera mensaje: "Saldaste con tu proveedor: Nombre Proveedor"
        """
        try:
            detalles_dict = {'proveedor_nombre': proveedor.nombre}
            if monto:
                detalles_dict['monto'] = str(monto)
            
            detalles_json = json.dumps(detalles_dict)
            
            RegistroAuditoria.objects.create(
                accion='saldar',
                usuario=usuario,
                tipo_contenido=ContentType.objects.get_for_model(proveedor.__class__),
                id_objeto=proveedor.pk,
                modelo='proveedor',
                descripcion_objeto=proveedor.nombre,
                detalles=detalles_json,
            )
            logger.info(f"Auditoría: {usuario} saldó con proveedor {proveedor.nombre}")
        except Exception as e:
            logger.error(f"Error registrando saldar proveedor: {e}", exc_info=True)
    
    @staticmethod
    def registrar_saldar_venta(venta, monto=None, usuario=None):
        """
        Registra cuando se salda una venta (pago del cliente).
        Genera mensaje: "Saldaste una venta con: Nombre del Cliente"
        """
        try:
            cliente_nombre = f"{venta.cliente.nombre} {venta.cliente.apellido}".strip() if venta.cliente else "Desconocido"
            detalles_dict = {'cliente_nombre': cliente_nombre}
            if monto:
                detalles_dict['monto'] = str(monto)
            
            detalles_json = json.dumps(detalles_dict)
            
            RegistroAuditoria.objects.create(
                accion='saldar',
                usuario=usuario,
                tipo_contenido=ContentType.objects.get_for_model(venta.__class__),
                id_objeto=venta.pk,
                modelo='venta',
                descripcion_objeto=cliente_nombre,
                detalles=detalles_json,
            )
            logger.info(f"Auditoría: {usuario} saldó venta con {cliente_nombre}")
        except Exception as e:
            logger.error(f"Error registrando saldar venta: {e}", exc_info=True)
    
    @staticmethod
    def registrar_pago(venta, monto, usuario=None):
        """
        Registra un pago/abono en una venta.
        Genera mensaje: "Saldaste una venta con: Nombre del Cliente ($monto)"
        """
        try:
            cliente_nombre = f"{venta.cliente.nombre} {venta.cliente.apellido}".strip() if venta.cliente else "Desconocido"
            detalles_dict = {'cliente_nombre': cliente_nombre, 'monto': str(monto)}
            detalles_json = json.dumps(detalles_dict)
            
            RegistroAuditoria.objects.create(
                accion='pagar',
                usuario=usuario,
                tipo_contenido=ContentType.objects.get_for_model(venta.__class__),
                id_objeto=venta.pk,
                modelo='venta',
                descripcion_objeto=cliente_nombre,
                detalles=detalles_json,
            )
            logger.info(f"Auditoría: {usuario} registró pago de ${monto} en venta de {cliente_nombre}")
        except Exception as e:
            logger.error(f"Error registrando pago: {e}", exc_info=True)
    
    @staticmethod
    def registrar_cambio_estado(objeto, estado_anterior, estado_nuevo, usuario):
        """
        Registra un cambio de estado en cualquier objeto.
        """
        try:
            detalles_dict = {
                'estado_anterior': estado_anterior,
                'nuevo_estado': estado_nuevo
            }
            detalles_json = json.dumps(detalles_dict)
            
            # Determinar el modelo
            modelo_map = {
                'Venta': 'venta',
                'Clientes': 'cliente',
                'Proveedores': 'proveedor',
                'Productos': 'producto',
                'Gastos': 'gasto',
            }
            modelo = modelo_map.get(objeto.__class__.__name__, 'desconocido')
            
            RegistroAuditoria.objects.create(
                accion='cambio_estado',
                usuario=usuario,
                tipo_contenido=ContentType.objects.get_for_model(objeto.__class__),
                id_objeto=objeto.pk,
                modelo=modelo,
                descripcion_objeto=str(objeto),
                detalles=detalles_json,
            )
            logger.info(f"Auditoría: {usuario} cambió estado de {objeto} a {estado_nuevo}")
        except Exception as e:
            logger.error(f"Error registrando cambio de estado: {e}", exc_info=True)
    
    @staticmethod
    def registrar_venta_manual(venta, usuario=None):
        """
        Registra manualmente una venta con todos sus detalles.
        Útil si el signal no se dispara (fallback).
        Genera mensaje: "Registraste una venta a Cliente - Producto x cantidad"
        """
        try:
            detalles_dict = {}
            
            if venta.cliente:
                detalles_dict['cliente_nombre'] = f"{venta.cliente.nombre} {venta.cliente.apellido}".strip()
            
            # Obtener detalles de la venta si existen
            try:
                detalles_venta = venta.detalles.all()
                if detalles_venta.exists():
                    productos = []
                    cantidad_total = 0
                    for detalle in detalles_venta:
                        productos.append(f"{detalle.producto.nombre} x{detalle.cantidad}")
                        cantidad_total += detalle.cantidad
                    
                    if productos:
                        detalles_dict['producto_nombre'] = ", ".join(productos)
                        detalles_dict['cantidad'] = str(cantidad_total)
                elif venta.producto:
                    detalles_dict['producto_nombre'] = venta.producto.nombre
                    detalles_dict['cantidad'] = str(venta.cantidad)
            except:
                if venta.producto:
                    detalles_dict['producto_nombre'] = venta.producto.nombre
                    detalles_dict['cantidad'] = str(venta.cantidad)
            
            detalles_dict['monto'] = str(venta.total)
            detalles_json = json.dumps(detalles_dict)
            
            RegistroAuditoria.objects.create(
                accion='crear',
                usuario=usuario,
                tipo_contenido=ContentType.objects.get_for_model(venta.__class__),
                id_objeto=venta.pk,
                modelo='venta',
                descripcion_objeto=str(venta),
                detalles=detalles_json,
            )
            logger.info(f"Auditoría manual: {usuario} registró venta #{venta.idVenta}")
        except Exception as e:
            logger.error(f"Error registrando venta manual: {e}", exc_info=True)

