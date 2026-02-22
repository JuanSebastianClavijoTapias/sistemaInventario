from django.shortcuts import render
from django.db.models import Sum, F
from apps.clientes.models import Clientes
from apps.proveedores.models import Proveedores
from apps.productos.models import Productos
from apps.ventas.models import Venta
from apps.gastos.models import Gastos

# Create your views here.
def saludo(request):
    # Calcular totales financieros
    total_ingresos = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    total_gastos = Gastos.objects.aggregate(total=Sum('monto'))['total'] or 0
    total_finanzas = total_ingresos - total_gastos
    
    # Calcular por cobrar: suma de saldos pendientes de ventas no pagadas
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
    
    context = {
        'total_clientes': Clientes.objects.count(),
        'total_proveedores': Proveedores.objects.count(),
        'total_productos': Productos.objects.count(),
        'total_ventas': Venta.objects.count(),
        'total_gastos': Gastos.objects.count(),
        'total_ingresos': total_ingresos,
        'total_gastos_finanzas': total_gastos,  # Renombrado para evitar conflicto
        'total_finanzas': total_finanzas,
        'total_por_cobrar': total_por_cobrar,
        'total_por_pagar': total_por_pagar,
        'ventas_pendientes': ventas_pendientes,
        'proveedores_pendientes': proveedores_pendientes,
    }
    print("Vista ejecutada, total_clientes:", context['total_clientes'])  # Temporal
    return render(request, 'index.html', context)

def ventas(request):
    return render(request, 'ventas.html')

def clientes(request):
    return render(request, 'clientes.html')

def proveedores(request):
    return render(request, 'proveedores.html')