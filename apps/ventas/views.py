from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
import calendar
import json
from decimal import Decimal
from .models import Venta
from apps.clientes.models import Clientes
from apps.productos.models import Productos

def ventas_form(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        producto_id = request.POST.get('producto')
        cantidad = request.POST.get('cantidad')
        tipo_pago = request.POST.get('tipo_pago', 'completo')
        monto_pagado = request.POST.get('monto_pagado', '0')
        dias_credito = request.POST.get('dias_credito', '15')
        
        if not cliente_id or not producto_id or not cantidad:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('ventas')
        
        try:
            cantidad = int(cantidad)
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número válido.')
            return redirect('ventas')
        
        try:
            cliente = Clientes.objects.get(idCliente=cliente_id)
            producto = Productos.objects.get(idProducto=producto_id)
        except (Clientes.DoesNotExist, Productos.DoesNotExist):
            messages.error(request, 'Cliente o producto no encontrado.')
            return redirect('ventas')
        
        # Verificar stock disponible
        if producto.stock < cantidad:
            messages.error(request, f'Stock insuficiente. Solo hay {producto.stock} unidades disponibles de {producto.nombre}.')
            return redirect('ventas')
        
        total = Decimal(str(producto.precio)) * Decimal(str(cantidad))
        
        # Procesar pago
        try:
            monto_pagado = Decimal(monto_pagado) if monto_pagado else Decimal('0')
        except (ValueError, TypeError):
            messages.error(request, 'El monto pagado debe ser un número válido.')
            return redirect('ventas')
        
        if tipo_pago == 'completo':
            monto_pagado = total
            fecha_vencimiento = None
            estado_pago = 'pagado'
        else:
            # Pago a crédito
            if monto_pagado > total:
                messages.error(request, 'El monto pagado no puede ser mayor al total de la venta.')
                return redirect('ventas')
            
            try:
                dias_credito = int(dias_credito)
            except ValueError:
                dias_credito = 15
            
            fecha_vencimiento = timezone.now().date() + timedelta(days=dias_credito)
            estado_pago = 'pendiente' if monto_pagado < total else 'pagado'
        
        # Crear la venta
        Venta.objects.create(
            cliente=cliente,
            producto=producto,
            cantidad=cantidad,
            total=total,
            tipo_pago=tipo_pago,
            monto_pagado=monto_pagado,
            fecha_vencimiento=fecha_vencimiento,
            estado_pago=estado_pago
        )
        
        # Descontar del stock
        producto.stock -= cantidad
        producto.save()
        
        if tipo_pago == 'completo':
            messages.success(request, f'Venta registrada exitosamente. Stock actualizado: {producto.nombre} - {producto.stock} unidades restantes.')
        else:
            saldo = total - monto_pagado
            messages.success(request, f'Venta a crédito registrada. Pagó: ${monto_pagado}, Debe: ${saldo}. Vence: {fecha_vencimiento}. Stock actualizado: {producto.nombre} - {producto.stock} unidades restantes.')
        
        return redirect('ventas')
    
    clientes = Clientes.objects.all()
    productos = Productos.objects.all()
    
    # Fecha actual
    hoy = timezone.now().date()
    
    # Actualizar estados de pago vencidos
    ventas_pendientes = Venta.objects.filter(estado_pago='pendiente')
    for venta in ventas_pendientes:
        venta.actualizar_estado_pago()
    
    # Calcular estadísticas del día
    ventas_hoy = Venta.objects.filter(fecha__date=hoy)
    total_ventas_dia = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_ventas_hoy = ventas_hoy.count()
    
    # Estadísticas de la semana (últimos 7 días)
    inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
    ventas_semana = Venta.objects.filter(fecha__date__gte=inicio_semana, fecha__date__lte=hoy)
    total_ventas_semana = ventas_semana.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_ventas_semana = ventas_semana.count()
    
    # Estadísticas del mes
    inicio_mes = hoy.replace(day=1)
    ventas_mes = Venta.objects.filter(fecha__date__gte=inicio_mes, fecha__date__lte=hoy)
    total_ventas_mes = ventas_mes.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_ventas_mes = ventas_mes.count()
    
    # Cliente que más ha comprado (este mes)
    top_cliente = Venta.objects.filter(
        fecha__date__gte=inicio_mes
    ).values(
        'cliente__nombre', 'cliente__apellido'
    ).annotate(
        total_compras=Sum('total'),
        cantidad_compras=Count('idVenta')
    ).order_by('-total_compras').first()
    
    # Total por cobrar (saldos pendientes de todas las ventas)
    total_por_cobrar = Venta.objects.filter(
        estado_pago__in=['pendiente', 'vencido']
    ).aggregate(
        total=Sum('total') - Sum('monto_pagado')
    )['total'] or 0
    
    # Datos del calendario - días con ventas este mes
    dias_con_ventas = Venta.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).values('fecha__day').annotate(
        total=Sum('total'),
        cantidad=Count('idVenta')
    ).distinct()
    
    # Convertir a diccionario para fácil acceso en JavaScript
    dias_ventas_dict = {
        item['fecha__day']: {
            'total': float(item['total']),
            'cantidad': item['cantidad']
        }
        for item in dias_con_ventas
    }
    
    # Información del calendario
    cal = calendar.Calendar(firstweekday=0)  # Lunes como primer día
    mes_actual = hoy.month
    anio_actual = hoy.year
    dias_del_mes = list(cal.itermonthdays(anio_actual, mes_actual))
    
    # Nombre del mes en español
    meses_espanol = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    nombre_mes = meses_espanol[mes_actual - 1]
    
    # Historial de ventas recientes
    ventas = Venta.objects.all().order_by('-fecha')[:20]
    
    # Alertas de vencimiento
    alertas = []
    ventas_por_vencer = Venta.objects.filter(
        estado_pago='pendiente',
        fecha_vencimiento__isnull=False
    )
    
    for venta in ventas_por_vencer:
        dias = venta.dias_para_vencimiento
        if dias is not None:
            if dias < 0:
                alertas.append({
                    'tipo': 'vencido',
                    'mensaje': f'Venta #{venta.idVenta} de {venta.cliente.nombre} {venta.cliente.apellido} está vencida desde hace {-dias} días. Debe: ${venta.saldo_pendiente}',
                    'venta': venta
                })
            elif dias <= 1:
                alertas.append({
                    'tipo': 'urgente',
                    'mensaje': f'Venta #{venta.idVenta} de {venta.cliente.nombre} {venta.cliente.apellido} vence {"hoy" if dias == 0 else "mañana"}. Debe: ${venta.saldo_pendiente}',
                    'venta': venta
                })
    
    context = {
        'clientes': clientes,
        'productos': productos,
        'ventas': ventas,
        'total_ventas_dia': total_ventas_dia,
        'cantidad_ventas_hoy': cantidad_ventas_hoy,
        'total_por_cobrar': total_por_cobrar,
        # Nuevas estadísticas
        'total_ventas_semana': total_ventas_semana,
        'cantidad_ventas_semana': cantidad_ventas_semana,
        'total_ventas_mes': total_ventas_mes,
        'cantidad_ventas_mes': cantidad_ventas_mes,
        'top_cliente': top_cliente,
        # Calendario
        'dias_ventas_json': json.dumps(dias_ventas_dict),
        'dias_del_mes': dias_del_mes,
        'nombre_mes': nombre_mes,
        'anio_actual': anio_actual,
        'dia_actual': hoy.day,
        # Alertas
        'alertas': alertas,
    }
    
    return render(request, 'ventas.html', context)
