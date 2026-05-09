from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from apps.auditoria.models import RegistroAuditoria, ConfiguracionAuditoria
from apps.clientes.models import Clientes
from apps.proveedores.models import Proveedores
from apps.productos.models import Productos
from apps.ventas.models import Venta
from apps.gastos.models import Gastos
import json
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Mapeo de modelos a sus nombres para auditoría
MODELOS_AUDITABLES = {
    Clientes: 'cliente',
    Proveedores: 'proveedor',
    Productos: 'producto',
    Venta: 'venta',
    Gastos: 'gasto',
}

# Mapeo de nombres de modelo para ConfiguracionAuditoria
MODELOS_CONFIG = {
    'Clientes': Clientes,
    'Proveedores': Proveedores,
    'Productos': Productos,
    'Ventas': Venta,  # Nota: 'Ventas' en la config pero 'Venta' es la clase
    'Gastos': Gastos,
}

# Almacenamiento temporal de valores anteriores
_valores_anteriores = {}


def obtener_descripcion_objeto(instancia):
    """
    Retorna una descripción legible del objeto.
    """
    if hasattr(instancia, '__str__'):
        return str(instancia)
    return f"{instancia.__class__.__name__} #{instancia.pk}"


def obtener_valores_objeto(instancia, excluir_campos=None):
    """
    Extrae todos los valores del objeto en formato serializable.
    """
    from datetime import datetime, date, time
    
    if excluir_campos is None:
        excluir_campos = ['id', 'pk']
    
    valores = {}
    for field in instancia._meta.fields:
        if field.name not in excluir_campos:
            try:
                valor = getattr(instancia, field.name)
                
                # Convertir tipos especiales a strings
                if isinstance(valor, Decimal):
                    valor = str(valor)
                elif isinstance(valor, (datetime, date, time)):
                    valor = valor.isoformat()
                elif hasattr(valor, 'pk'):  # ForeignKey
                    valor = valor.pk if valor else None
                
                valores[field.name] = valor
            except:
                pass
    
    return valores


def registrar_auditoria(instancia, accion, usuario=None, detalles="", 
                        valores_antes=None, valores_despues=None, 
                        campos_modificados=None):
    """
    Registra una acción de auditoría.
    """
    try:
        # Verificar que la auditoría esté activa
        modelo_clase = instancia.__class__
        modelo_nombre = MODELOS_AUDITABLES.get(modelo_clase)
        
        if not modelo_nombre:
            return
        
        # Verificar configuración
        config_activo = True
        auditar_creacion = True
        auditar_edicion = True
        auditar_eliminacion = True
        
        try:
            # Buscar en ConfiguracionAuditoria
            config = ConfiguracionAuditoria.objects.filter(
                modelo=modelo_clase.__name__
            ).first()
            
            # Si no existe con el nombre exacto de la clase, buscar alternativas
            if not config:
                for config_name, config_class in MODELOS_CONFIG.items():
                    if config_class == modelo_clase:
                        config = ConfiguracionAuditoria.objects.filter(
                            modelo=config_name
                        ).first()
                        break
            
            if config:
                config_activo = config.activo
                auditar_creacion = config.auditar_creacion
                auditar_edicion = config.auditar_edicion
                auditar_eliminacion = config.auditar_eliminacion
        except Exception as e:
            logger.warning(f"Error obteniendo ConfiguracionAuditoria: {e}")
            # Si hay error, asumir que está activo
            pass
        
        # Si no está activa la auditoría general, no registrar
        if not config_activo:
            return
        
        # Verificar según el tipo de acción
        if accion == 'crear' and not auditar_creacion:
            return
        elif accion == 'editar' and not auditar_edicion:
            return
        elif accion == 'eliminar' and not auditar_eliminacion:
            return
        
        # Obtener tipo de contenido
        content_type = ContentType.objects.get_for_model(modelo_clase)
        
        # Preparar valores
        if valores_antes is None:
            valores_antes = {}
        if valores_despues is None:
            valores_despues = {}
        if campos_modificados is None:
            campos_modificados = []
        
        # Crear registro de auditoría
        RegistroAuditoria.objects.create(
            accion=accion,
            usuario=usuario,
            tipo_contenido=content_type,
            id_objeto=instancia.pk,
            modelo=modelo_nombre,
            descripcion_objeto=obtener_descripcion_objeto(instancia),
            valores_antes=valores_antes,
            valores_despues=valores_despues,
            campos_modificados=campos_modificados,
            detalles=detalles,
        )
        logger.info(f"Auditoría registrada: {accion} en {modelo_nombre} #{instancia.pk}")
    except Exception as e:
        logger.error(f"Error registrando auditoría: {str(e)}", exc_info=True)


@receiver(pre_save, sender=Clientes)
@receiver(pre_save, sender=Proveedores)
@receiver(pre_save, sender=Productos)
@receiver(pre_save, sender=Venta)
@receiver(pre_save, sender=Gastos)
def guardar_valores_anteriores(sender, instance, **kwargs):
    """
    Guarda los valores anteriores antes de que se guarde la instancia.
    """
    if instance.pk:  # Solo si el objeto ya existe
        try:
            objeto_anterior = sender.objects.get(pk=instance.pk)
            valores_anteriores = obtener_valores_objeto(objeto_anterior)
            _valores_anteriores[id(instance)] = valores_anteriores
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Venta)
def registrar_venta_post_save(sender, instance, created, **kwargs):
    """
    Registra la creación/edición de una venta con detalles de productos.
    """
    try:
        usuario = getattr(instance, '_usuario_auditoria', None)
        detalles_dict = {}
        
        # Extraer información de la venta
        if instance.cliente:
            detalles_dict['cliente_nombre'] = f"{instance.cliente.nombre} {instance.cliente.apellido}".strip()
        
        # Si la venta tiene detalles (DetalleVenta), obtenerlos
        try:
            detalles_venta = instance.detalles.all()
            if detalles_venta.exists():
                # Productos y cantidades
                productos = []
                cantidad_total = 0
                for detalle in detalles_venta:
                    productos.append(f"{detalle.producto.nombre} x{detalle.cantidad}")
                    cantidad_total += detalle.cantidad
                
                if productos:
                    detalles_dict['producto_nombre'] = ", ".join(productos)
                    detalles_dict['cantidad'] = str(cantidad_total)
            elif instance.producto:
                # Si no hay detalles pero tiene producto directo (caso simple)
                detalles_dict['producto_nombre'] = instance.producto.nombre
                detalles_dict['cantidad'] = str(instance.cantidad)
        except:
            # Si no funciona, usar producto directo
            if instance.producto:
                detalles_dict['producto_nombre'] = instance.producto.nombre
                detalles_dict['cantidad'] = str(instance.cantidad)
        
        detalles_dict['monto'] = str(instance.total)
        
        import json
        detalles_json = json.dumps(detalles_dict)
        
        if created:
            # Objeto recién creado
            valores_despues = obtener_valores_objeto(instance)
            registrar_auditoria(
                instance,
                accion='crear',
                usuario=usuario,
                valores_despues=valores_despues,
                detalles=detalles_json
            )
        else:
            # Objeto editado
            valores_anteriores = _valores_anteriores.pop(id(instance), {})
            valores_nuevos = obtener_valores_objeto(instance)
            
            campos_modificados = [
                campo for campo in valores_nuevos.keys()
                if valores_anteriores.get(campo) != valores_nuevos.get(campo)
            ]
            
            if campos_modificados:
                registrar_auditoria(
                    instance,
                    accion='editar',
                    usuario=usuario,
                    valores_antes=valores_anteriores,
                    valores_despues=valores_nuevos,
                    campos_modificados=campos_modificados,
                    detalles=detalles_json
                )
    except Exception as e:
        logger.error(f"Error en registrar_venta_post_save: {str(e)}", exc_info=True)


@receiver(post_save, sender=Clientes)
@receiver(post_save, sender=Proveedores)
@receiver(post_save, sender=Productos)
def registrar_cambios_productos(sender, instance, created, **kwargs):
    """
    Registra cambios en Productos, pero ignora cambios de stock únicamente.
    """
    try:
        # Si hay marca para saltarse, hacerlo
        if getattr(instance, '_auditoria_skip', False):
            return
        
        usuario = getattr(instance, '_usuario_auditoria', None)
        detalles_dict = {}
        
        import json
        detalles_json = json.dumps(detalles_dict) if detalles_dict else ""
        
        if created:
            # Producto recién creado
            valores_despues = obtener_valores_objeto(instance)
            registrar_auditoria(
                instance,
                accion='crear',
                usuario=usuario,
                valores_despues=valores_despues,
                detalles=detalles_json
            )
        else:
            # Producto editado
            valores_anteriores = _valores_anteriores.pop(id(instance), {})
            valores_nuevos = obtener_valores_objeto(instance)
            
            # Detectar campos modificados (excluyendo stock)
            campos_modificados = [
                campo for campo in valores_nuevos.keys()
                if campo != 'stock' and valores_anteriores.get(campo) != valores_nuevos.get(campo)
            ]
            
            # Solo registrar si hubo cambios que NO sean solo stock
            if campos_modificados:
                registrar_auditoria(
                    instance,
                    accion='editar',
                    usuario=usuario,
                    valores_antes=valores_anteriores,
                    valores_despues=valores_nuevos,
                    campos_modificados=campos_modificados,
                    detalles=detalles_json
                )
    except Exception as e:
        logger.error(f"Error en registrar_cambios_productos: {str(e)}", exc_info=True)


@receiver(post_save, sender=Gastos)
def registrar_cambios_gastos(sender, instance, created, **kwargs):
    """
    Registra cambios en Gastos.
    """
    try:
        usuario = getattr(instance, '_usuario_auditoria', None)
        detalles_dict = {}
        
        if hasattr(instance, 'monto'):
            detalles_dict['monto'] = str(instance.monto)
        
        import json
        detalles_json = json.dumps(detalles_dict) if detalles_dict else ""
        
        if created:
            valores_despues = obtener_valores_objeto(instance)
            registrar_auditoria(
                instance,
                accion='crear',
                usuario=usuario,
                valores_despues=valores_despues,
                detalles=detalles_json
            )
        else:
            valores_anteriores = _valores_anteriores.pop(id(instance), {})
            valores_nuevos = obtener_valores_objeto(instance)
            
            campos_modificados = [
                campo for campo in valores_nuevos.keys()
                if valores_anteriores.get(campo) != valores_nuevos.get(campo)
            ]
            
            if campos_modificados:
                registrar_auditoria(
                    instance,
                    accion='editar',
                    usuario=usuario,
                    valores_antes=valores_anteriores,
                    valores_despues=valores_nuevos,
                    campos_modificados=campos_modificados,
                    detalles=detalles_json
                )
    except Exception as e:
        logger.error(f"Error en registrar_cambios_gastos: {str(e)}", exc_info=True)


@receiver(post_delete, sender=Venta)
def registrar_venta_eliminacion(sender, instance, **kwargs):
    """
    Registra la eliminación de una venta con detalles.
    """
    try:
        usuario = getattr(instance, '_usuario_auditoria', None)
        valores_antes = obtener_valores_objeto(instance)
        
        # Preparar detalles enriquecidos
        detalles_dict = {}
        
        if instance.cliente:
            detalles_dict['cliente_nombre'] = f"{instance.cliente.nombre} {instance.cliente.apellido}".strip()
        if instance.producto:
            detalles_dict['producto_nombre'] = instance.producto.nombre
        
        import json
        detalles_json = json.dumps(detalles_dict) if detalles_dict else ""
        
        registrar_auditoria(
            instance,
            accion='eliminar',
            usuario=usuario,
            valores_antes=valores_antes,
            detalles=detalles_json
        )
    except Exception as e:
        logger.error(f"Error en registrar_venta_eliminacion: {str(e)}", exc_info=True)


@receiver(post_delete, sender=Clientes)
@receiver(post_delete, sender=Proveedores)
@receiver(post_delete, sender=Productos)
@receiver(post_delete, sender=Gastos)
def registrar_eliminacion(sender, instance, **kwargs):
    """
    Registra la eliminación de un objeto (excluyendo Venta que tiene su propio handler).
    """
    try:
        usuario = getattr(instance, '_usuario_auditoria', None)
        valores_antes = obtener_valores_objeto(instance)
        
        # Preparar detalles enriquecidos
        detalles_dict = {}
        
        if sender == Proveedores:
            detalles_dict['proveedor_nombre'] = instance.nombre if hasattr(instance, 'nombre') else str(instance)
        elif sender == Clientes:
            detalles_dict['cliente_nombre'] = f"{instance.nombre} {instance.apellido}".strip()
        
        import json
        detalles_json = json.dumps(detalles_dict) if detalles_dict else ""
        
        registrar_auditoria(
            instance,
            accion='eliminar',
            usuario=usuario,
            valores_antes=valores_antes,
            detalles=detalles_json
        )
    except Exception as e:
        logger.error(f"Error en registrar_eliminacion: {str(e)}", exc_info=True)
