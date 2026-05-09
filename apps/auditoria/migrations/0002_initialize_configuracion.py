# Generated migration to initialize ConfiguracionAuditoria

from django.db import migrations


def create_default_config(apps, schema_editor):
    """
    Crea los registros de configuración de auditoría por defecto.
    """
    ConfiguracionAuditoria = apps.get_model('auditoria', 'ConfiguracionAuditoria')
    
    modelos = [
        ('Clientes', True, True, True, True),
        ('Proveedores', True, True, True, True),
        ('Productos', True, True, True, True),
        ('Ventas', True, True, True, True),
        ('Gastos', True, True, True, True),
    ]
    
    for modelo, activo, auditar_creacion, auditar_edicion, auditar_eliminacion in modelos:
        ConfiguracionAuditoria.objects.get_or_create(
            modelo=modelo,
            defaults={
                'activo': activo,
                'auditar_creacion': auditar_creacion,
                'auditar_edicion': auditar_edicion,
                'auditar_eliminacion': auditar_eliminacion,
            }
        )


def reverse_config(apps, schema_editor):
    """
    Elimina los registros de configuración de auditoría.
    """
    ConfiguracionAuditoria = apps.get_model('auditoria', 'ConfiguracionAuditoria')
    ConfiguracionAuditoria.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_config, reverse_config),
    ]
