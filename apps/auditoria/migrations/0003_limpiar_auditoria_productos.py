# Migration para limpiar registros de auditoría de productos incorrectos

from django.db import migrations


def limpiar_auditoria_productos(apps, schema_editor):
    """
    Elimina registros de auditoría de productos que solo muestran cambios de stock.
    Estos registros fueron generados por el sistema al actualizar stock durante ventas,
    y no deberían aparecer en el historial.
    """
    RegistroAuditoria = apps.get_model('auditoria', 'RegistroAuditoria')
    
    # Eliminar registros donde:
    # - La acción fue 'editar' (edición)
    # - El modelo es 'producto' (producto)
    # - Se editó el producto (claramente cambios de stock)
    registros_a_eliminar = RegistroAuditoria.objects.filter(
        accion='editar',
        modelo='producto'
    )
    
    cantidad_eliminados = registros_a_eliminar.count()
    registros_a_eliminar.delete()
    
    print(f"✓ Se eliminaron {cantidad_eliminados} registros incorrectos de auditoría de productos")


def reverse_limpiar(apps, schema_editor):
    """
    No se puede revertir esta limpieza, pero dejamos el placeholder.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0002_initialize_configuracion'),
    ]

    operations = [
        migrations.RunPython(limpiar_auditoria_productos, reverse_limpiar),
    ]
