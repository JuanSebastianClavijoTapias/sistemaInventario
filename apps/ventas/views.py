from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
import calendar
import json
from decimal import Decimal
from .models import Venta, DetalleVenta
from apps.clientes.models import Clientes
from apps.productos.models import Productos

def ventas_form(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        tipo_pago = request.POST.get('tipo_pago', 'completo')
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')
        monto_pagado = request.POST.get('monto_pagado', '0')
        dias_credito = request.POST.get('dias_credito', '15')

        # Multi-item data
        productos_ids = request.POST.getlist('producto[]')
        cantidades = request.POST.getlist('cantidad[]')
        precios_venta = request.POST.getlist('precio_venta[]')

        if not cliente_id or not productos_ids or not any(productos_ids):
            messages.error(request, 'Debe seleccionar un cliente y al menos un producto.')
            return redirect('ventas')

        try:
            cliente = Clientes.objects.get(idCliente=cliente_id)
        except Clientes.DoesNotExist:
            messages.error(request, 'Cliente no encontrado.')
            return redirect('ventas')

        # Process items
        items = []
        for i in range(len(productos_ids)):
            if not productos_ids[i] or not cantidades[i]:
                continue
            try:
                producto = Productos.objects.get(idProducto=int(productos_ids[i]))
                cantidad = int(cantidades[i])
                precio_venta_input = Decimal(precios_venta[i]) if i < len(precios_venta) and precios_venta[i] else Decimal('0')
            except (Productos.DoesNotExist, ValueError):
                messages.error(request, 'Producto o cantidad inválida.')
                return redirect('ventas')

            if cantidad <= 0 or precio_venta_input <= 0:
                continue

            if producto.stock < cantidad:
                messages.error(request, f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}')
                return redirect('ventas')

            precio_compra = Decimal(str(producto.precio_compra))
            precio_venta = precio_venta_input
            subtotal = precio_venta * Decimal(str(cantidad))
            ganancia = (precio_venta - precio_compra) * Decimal(str(cantidad))

            items.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio_compra': precio_compra,
                'precio_venta': precio_venta,
                'subtotal': subtotal,
                'ganancia': ganancia,
            })

        if not items:
            messages.error(request, 'Debe agregar al menos un producto válido.')
            return redirect('ventas')

        # Calculate totals
        total = sum(item['subtotal'] for item in items)
        total_ganancia = sum(item['ganancia'] for item in items)
        total_cantidad = sum(item['cantidad'] for item in items)

        # Process payment
        try:
            monto_pagado_val = Decimal(monto_pagado) if monto_pagado else Decimal('0')
        except (ValueError, TypeError):
            messages.error(request, 'El monto pagado debe ser un número válido.')
            return redirect('ventas')

        if tipo_pago == 'completo':
            monto_pagado_val = total
            fecha_vencimiento = None
            estado_pago = 'pagado'
        else:
            if monto_pagado_val > total:
                messages.error(request, 'El monto pagado no puede ser mayor al total de la venta.')
                return redirect('ventas')
            try:
                dias_credito = int(dias_credito)
            except ValueError:
                dias_credito = 15
            fecha_vencimiento = timezone.localdate() + timedelta(days=dias_credito)
            estado_pago = 'pendiente' if monto_pagado_val < total else 'pagado'

        is_single = len(items) == 1

        # Create the sale
        venta = Venta.objects.create(
            cliente=cliente,
            producto=items[0]['producto'] if is_single else None,
            cantidad=total_cantidad,
            total=total,
            precio_compra=items[0]['precio_compra'] if is_single else Decimal('0'),
            precio_venta=items[0]['precio_venta'] if is_single else Decimal('0'),
            ganancia=total_ganancia,
            tipo_pago=tipo_pago,
            metodo_pago=metodo_pago,
            monto_pagado=monto_pagado_val,
            fecha_vencimiento=fecha_vencimiento,
            estado_pago=estado_pago
        )

        # Create detail records and update stock
        for item in items:
            DetalleVenta.objects.create(
                venta=venta,
                producto=item['producto'],
                cantidad=item['cantidad'],
                precio_compra=item['precio_compra'],
                precio_venta=item['precio_venta'],
                subtotal=item['subtotal'],
                ganancia=item['ganancia'],
            )
            item['producto'].stock -= item['cantidad']
            item['producto'].save()

        if tipo_pago == 'completo':
            messages.success(request, f'Venta registrada. Total: ${total:,.0f}, Ganancia: ${total_ganancia:,.0f}')
        else:
            saldo = total - monto_pagado_val
            messages.success(request, f'Venta a crédito. Pagó: ${monto_pagado_val:,.0f}, Debe: ${saldo:,.0f}. Vence: {fecha_vencimiento}.')

        return redirect('ventas')
    
    clientes = Clientes.objects.all()
    productos = Productos.objects.all()
    
    # Fecha actual (usa zona horaria local)
    hoy = timezone.localdate()
    
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
    
    # Lista detallada de ventas del mes para el modal
    ventas_mes = Venta.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).select_related('cliente', 'producto').prefetch_related('detalles', 'detalles__producto').order_by('-fecha')
    
    ventas_mes_lista = [
        {
            'dia': venta.fecha.day,
            'producto': venta.descripcion,
            'cliente': f"{venta.cliente.nombre} {venta.cliente.apellido}",
            'cantidad': venta.cantidad,
            'total': float(venta.total),
            'hora': venta.fecha.strftime('%H:%M'),
            'metodo_pago': venta.get_metodo_pago_display(),
        }
        for venta in ventas_mes
    ]
    
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
    
    # Filtro de rango para historial
    rango_filtro = request.GET.get('rango', 'todo')
    
    # Historial de ventas con filtro
    ventas_query = Venta.objects.all().select_related('cliente', 'producto').prefetch_related('detalles', 'detalles__producto').order_by('-fecha')
    
    if rango_filtro == 'hoy':
        ventas_query = ventas_query.filter(fecha__date=hoy)
    elif rango_filtro == 'semana':
        inicio_semana_filtro = hoy - timedelta(days=7)
        ventas_query = ventas_query.filter(fecha__date__gte=inicio_semana_filtro)
    elif rango_filtro == 'quincena':
        inicio_quincena = hoy - timedelta(days=15)
        ventas_query = ventas_query.filter(fecha__date__gte=inicio_quincena)
    elif rango_filtro == 'mes':
        ventas_query = ventas_query.filter(fecha__date__gte=inicio_mes)
    # 'todo' no filtra nada
    
    ventas = ventas_query[:50]  # Limitar a 50 resultados
    
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
        'ventas_mes_json': json.dumps(ventas_mes_lista),
        'dias_del_mes': dias_del_mes,
        'nombre_mes': nombre_mes,
        'anio_actual': anio_actual,
        'dia_actual': hoy.day,
        # Alertas
        'alertas': alertas,
        # Filtro de rango
        'rango_filtro': rango_filtro,
    }
    
    return render(request, 'ventas.html', context)
