from django.contrib import admin
from .models import LiquidacionSemanal, ConfiguracionSemana, Suscripcion

# Register your models here.

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'estado', 'fecha_vencimiento', 'dias_restantes', 'fecha_ultimo_pago')
    list_filter = ('estado',)
    list_editable = ('estado', 'fecha_vencimiento')
    
    def dias_restantes(self, obj):
        return obj.dias_restantes
    dias_restantes.short_description = "Días Restantes"


@admin.register(LiquidacionSemanal)
class LiquidacionSemanalAdmin(admin.ModelAdmin):
    list_display = ('numero_semana', 'anio', 'fecha_inicio', 'fecha_fin', 'balance_final')


@admin.register(ConfiguracionSemana)
class ConfiguracionSemanaAdmin(admin.ModelAdmin):
    list_display = ('fecha_inicio_semana_actual', 'dias_por_semana')
