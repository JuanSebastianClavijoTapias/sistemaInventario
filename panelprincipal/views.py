from django.shortcuts import render, redirect
from django.db.models import Sum, F, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.utils import timezone
from datetime import timedelta
from apps.clientes.models import Clientes
from apps.proveedores.models import Proveedores
from apps.productos.models import Productos
from apps.ventas.models import Venta
from apps.gastos.models import Gastos
from .models import LiquidacionSemanal, ConfiguracionSemana


def obtener_semana_actual():
    """Obtiene o crea la configuración de semana actual"""
    config = ConfiguracionSemana.objects.first()
    if not config:
        # Buscar la fecha de la primera venta para no perder datos existentes
        primera_venta = Venta.objects.order_by('fecha').first()
        if primera_venta:
            fecha_inicio = primera_venta.fecha.date()
        else:
            fecha_inicio = timezone.localdate()
        
        config = ConfiguracionSemana.objects.create(
            fecha_inicio_semana_actual=fecha_inicio,
            dias_por_semana=8
        )
    return config


def calcular_datos_semana(fecha_inicio, fecha_fin):
    """Calcula los datos financieros para un rango de fechas"""
    # Filtrar ventas de la semana
    ventas_semana = Venta.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    )
    
    # Filtrar gastos de la semana
    gastos_semana = Gastos.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    )
    
    # Calcular totales
    total_ingresos = ventas_semana.aggregate(total=Sum('total'))['total'] or 0
    total_gastos = gastos_semana.aggregate(total=Sum('monto'))['total'] or 0
    total_finanzas = total_ingresos - total_gastos
    total_recaudado = ventas_semana.aggregate(total=Sum('monto_pagado'))['total'] or 0
    
    # Ventas a crédito
    ventas_credito = ventas_semana.filter(tipo_pago='fiado')
    total_ventas_credito = ventas_credito.aggregate(total=Sum('total'))['total'] or 0
    cantidad_ventas_credito = ventas_credito.count()
    cobrado_de_creditos = ventas_credito.aggregate(total=Sum('monto_pagado'))['total'] or 0
    pendiente_creditos = total_ventas_credito - cobrado_de_creditos
    
    # Ventas pago completo
    ventas_completo = ventas_semana.filter(tipo_pago='completo')
    total_ventas_completo = ventas_completo.aggregate(total=Sum('total'))['total'] or 0
    cantidad_ventas_completo = ventas_completo.count()
    
    # Ganancia
    total_ganancia = ventas_semana.aggregate(total=Sum('ganancia'))['total'] or 0
    
    # Balance real = solo dinero efectivamente cobrado - gastos
    balance_real = total_recaudado - total_gastos
    
    return {
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'total_finanzas': total_finanzas,
        'total_recaudado': total_recaudado,
        'balance_real': balance_real,
        'total_ventas_credito': total_ventas_credito,
        'cantidad_ventas_credito': cantidad_ventas_credito,
        'cobrado_de_creditos': cobrado_de_creditos,
        'pendiente_creditos': pendiente_creditos,
        'total_ventas_completo': total_ventas_completo,
        'cantidad_ventas_completo': cantidad_ventas_completo,
        'total_ganancia': total_ganancia,
        'cantidad_ventas': ventas_semana.count(),
    }


# Create your views here.
def saludo(request):
    # Obtener configuración de semana actual
    config_semana = obtener_semana_actual()
    fecha_inicio = config_semana.lunes_semana_actual
    fecha_fin = config_semana.domingo_semana_actual
    
    # Calcular datos de la semana actual
    datos_semana = calcular_datos_semana(fecha_inicio, fecha_fin)
    
    # Calcular por cobrar: suma de saldos pendientes de ventas no pagadas (general)
    total_por_cobrar = Venta.objects.filter(estado_pago__in=['pendiente', 'vencido']).aggregate(
        total=Sum(F('total') - F('monto_pagado'))
    )['total'] or 0
    
    # Calcular por pagar: suma de saldos de proveedores
    total_por_pagar = Proveedores.objects.aggregate(total=Sum('saldo'))['total'] or 0
    
    # Obtener ventas pendientes por cliente (para lista de por cobrar)
    ventas_pendientes = Venta.objects.filter(
        estado_pago__in=['pendiente', 'vencido']
    ).select_related('cliente', 'producto').order_by('fecha_vencimiento')
    
    # Obtener proveedores con saldo pendiente (para lista de por pagar)
    proveedores_pendientes = Proveedores.objects.filter(saldo__gt=0).order_by('-saldo')
    
    # Última liquidación
    ultima_liquidacion = LiquidacionSemanal.objects.first()
    
    context = {
        'total_clientes': Clientes.objects.count(),
        'total_proveedores': Proveedores.objects.count(),
        'total_productos': Productos.objects.count(),
        'total_ventas': datos_semana['cantidad_ventas'],
        'total_gastos': Gastos.objects.filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).count(),
        'total_por_cobrar': total_por_cobrar,
        'total_por_pagar': total_por_pagar,
        'ventas_pendientes': ventas_pendientes,
        'proveedores_pendientes': proveedores_pendientes,
        # Datos de la semana actual
        'total_ingresos': datos_semana['total_ingresos'],
        'total_gastos_finanzas': datos_semana['total_gastos'],
        'total_finanzas': datos_semana['total_finanzas'],
        'total_recaudado': datos_semana['total_recaudado'],
        'total_ventas_credito': datos_semana['total_ventas_credito'],
        'cantidad_ventas_credito': datos_semana['cantidad_ventas_credito'],
        'cobrado_de_creditos': datos_semana['cobrado_de_creditos'],
        'pendiente_creditos': datos_semana['pendiente_creditos'],
        'total_ventas_completo': datos_semana['total_ventas_completo'],
        'cantidad_ventas_completo': datos_semana['cantidad_ventas_completo'],
        'total_ganancia': datos_semana['total_ganancia'],
        # Info de la semana
        'fecha_inicio_semana': fecha_inicio,
        'fecha_fin_semana': fecha_fin,
        'dias_restantes': config_semana.dias_restantes,
        'ultima_liquidacion': ultima_liquidacion,
    }
    return render(request, 'index.html', context)


def liquidar_semana(request):
    """Vista para realizar la liquidación semanal"""
    if request.method == 'POST':
        config_semana = obtener_semana_actual()
        fecha_inicio = config_semana.lunes_semana_actual
        fecha_fin = config_semana.domingo_semana_actual
        
        # Calcular datos de la semana
        datos = calcular_datos_semana(fecha_inicio, fecha_fin)
        
        # Obtener número de semana del año
        numero_semana = fecha_inicio.isocalendar()[1]
        anio = fecha_inicio.year
        
        # Verificar si ya existe una liquidación para esta semana
        if LiquidacionSemanal.objects.filter(numero_semana=numero_semana, anio=anio).exists():
            messages.warning(request, f'La semana {numero_semana} del {anio} ya fue liquidada.')
            return redirect('inicio')
        
        # Crear la liquidación
        LiquidacionSemanal.objects.create(
            numero_semana=numero_semana,
            anio=anio,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_ingresos=datos['total_ingresos'],
            total_ventas_completo=datos['total_ventas_completo'],
            total_ventas_credito=datos['total_ventas_credito'],
            total_recaudado=datos['total_recaudado'],
            cobrado_de_creditos=datos['cobrado_de_creditos'],
            total_gastos=datos['total_gastos'],
            total_ganancia=datos['total_ganancia'],
            balance_final=datos['balance_real'],
            cantidad_ventas=datos['cantidad_ventas'],
            cantidad_ventas_completo=datos['cantidad_ventas_completo'],
            cantidad_ventas_credito=datos['cantidad_ventas_credito'],
        )
        
        messages.success(request, f'Semana {numero_semana} liquidada exitosamente. Balance: ${datos["total_finanzas"]}')
        return redirect('inicio')
    
    # GET - Mostrar confirmación
    config_semana = obtener_semana_actual()
    datos = calcular_datos_semana(
        config_semana.lunes_semana_actual,
        config_semana.domingo_semana_actual
    )
    
    context = {
        'datos': datos,
        'fecha_inicio': config_semana.lunes_semana_actual,
        'fecha_fin': config_semana.domingo_semana_actual,
    }
    return render(request, 'liquidar_semana.html', context)


def historial_semanas(request):
    """Vista para ver el historial de liquidaciones"""
    liquidaciones = LiquidacionSemanal.objects.all()
    
    # Totales históricos - usar total_recaudado en vez de total_ingresos
    # porque las deudas de clientes no son plata que haya entrado
    totales = liquidaciones.aggregate(
        total_recaudado=Sum('total_recaudado'),
        total_gastos=Sum('total_gastos'),
        total_ganancia=Sum('total_ganancia'),
        total_balance=Sum('balance_final'),
        total_pendiente=Sum(F('total_ventas_credito') - F('cobrado_de_creditos')),
    )
    
    context = {
        'liquidaciones': liquidaciones,
        'totales': totales,
    }
    return render(request, 'historial_semanas.html', context)


def detalle_semana(request, pk):
    """Vista para ver el detalle de una liquidación específica"""
    liquidacion = LiquidacionSemanal.objects.get(pk=pk)
    
    context = {
        'liquidacion': liquidacion,
    }
    return render(request, 'detalle_semana.html', context)


def ventas(request):
    return render(request, 'ventas.html')

def clientes(request):
    return render(request, 'clientes.html')

def proveedores(request):
    return render(request, 'proveedores.html')


@login_not_required
def cuenta_suspendida(request):
    """Vista que se muestra cuando la suscripción está vencida o suspendida"""
    return render(request, 'cuenta_suspendida.html')