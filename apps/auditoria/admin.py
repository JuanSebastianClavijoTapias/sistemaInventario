from django.contrib import admin
from apps.auditoria.models import RegistroAuditoria, ConfiguracionAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'accion', 'usuario', 'modelo', 'descripcion_objeto')
    list_filter = ('accion', 'modelo', 'fecha_hora', 'usuario')
    search_fields = ('descripcion_objeto', 'detalles', 'usuario__username')
    readonly_fields = ('fecha_hora', 'tipo_contenido', 'id_objeto', 'valores_antes', 'valores_despues')
    
    fieldsets = (
        ('Información de la Acción', {
            'fields': ('accion', 'usuario', 'fecha_hora')
        }),
        ('Objeto Afectado', {
            'fields': ('tipo_contenido', 'id_objeto', 'modelo', 'descripcion_objeto')
        }),
        ('Cambios Realizados', {
            'fields': ('campos_modificados', 'valores_antes', 'valores_despues'),
            'classes': ('collapse',)
        }),
        ('Detalles', {
            'fields': ('detalles', 'ip_cliente'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracionAuditoria)
class ConfiguracionAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'auditar_creacion', 'auditar_edicion', 'auditar_eliminacion', 'activo')
    list_editable = ('auditar_creacion', 'auditar_edicion', 'auditar_eliminacion', 'activo')
