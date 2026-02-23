from django.db import models
from django.utils import timezone

# Create your models here.

class LiquidacionSemanal(models.Model):
    """Modelo para guardar el historial de liquidaciones semanales"""
    
    numero_semana = models.IntegerField(verbose_name="Número de Semana")
    anio = models.IntegerField(verbose_name="Año")
    fecha_inicio = models.DateField(verbose_name="Fecha Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha Fin")
    fecha_liquidacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Liquidación")
    
    # Totales de ventas
    total_ingresos = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Ingresos")
    total_ventas_completo = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Ventas Pago Completo")
    total_ventas_credito = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Ventas a Crédito")
    total_recaudado = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Recaudado")
    cobrado_de_creditos = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Cobrado de Créditos")
    
    # Gastos
    total_gastos = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Gastos")
    
    # Ganancia
    total_ganancia = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Ganancia Total")
    
    # Balance final
    balance_final = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Balance Final")
    
    # Contadores
    cantidad_ventas = models.IntegerField(default=0, verbose_name="Cantidad de Ventas")
    cantidad_ventas_completo = models.IntegerField(default=0, verbose_name="Cantidad Ventas Completo")
    cantidad_ventas_credito = models.IntegerField(default=0, verbose_name="Cantidad Ventas Crédito")
    
    # Notas opcionales
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Liquidación Semanal"
        verbose_name_plural = "Liquidaciones Semanales"
        ordering = ['-fecha_liquidacion']
        unique_together = ['numero_semana', 'anio']
    
    def __str__(self):
        return f"Semana {self.numero_semana} - {self.anio} (${self.balance_final})"


class ConfiguracionSemana(models.Model):
    """Configuración para rastrear la semana actual"""
    
    fecha_inicio_semana_actual = models.DateField(verbose_name="Inicio Semana Actual", null=True, blank=True)
    dias_por_semana = models.IntegerField(default=7, verbose_name="Días por Semana")
    
    class Meta:
        verbose_name = "Configuración de Semana"
        verbose_name_plural = "Configuración de Semanas"
    
    def __str__(self):
        return f"Semana desde {self.fecha_inicio_semana_actual}"
    
    @property
    def lunes_semana_actual(self):
        """Calcula el lunes de la semana actual"""
        hoy = timezone.localdate()
        # weekday() devuelve 0 para lunes, 6 para domingo
        dias_desde_lunes = hoy.weekday()
        from datetime import timedelta
        return hoy - timedelta(days=dias_desde_lunes)
    
    @property
    def domingo_semana_actual(self):
        """Calcula el domingo de la semana actual"""
        from datetime import timedelta
        return self.lunes_semana_actual + timedelta(days=6)
    
    @property
    def fecha_fin_semana_actual(self):
        return self.domingo_semana_actual
    
    @property
    def dias_restantes(self):
        hoy = timezone.localdate()
        fin = self.domingo_semana_actual
        dias = (fin - hoy).days
        return max(0, dias + 1)

