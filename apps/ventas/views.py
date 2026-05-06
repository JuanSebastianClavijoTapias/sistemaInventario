from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import transaction
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import timedelta
import calendar
import json
from decimal import Decimal
from .models import Venta, DetalleVenta, Cobro
from .forms import VentaForm, DetalleVentaForm, CobroForm, EditarVentaForm
from apps.clientes.models import Clientes
from apps.productos.models import Productos

def ventas_form(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        dias_credito = request.POST.get('dias_credito', '15')

        # Montos de pago
        try:
            monto_efectivo = Decimal(request.POST.get('monto_efectivo', '0') or '0')
            monto_transferencia = Decimal(request.POST.get('monto_transferencia', '0') or '0')
        except Exception:
            messages.error(request, 'Los montos de pago deben ser números válidos.')
            return redirect('ventas')

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
        monto_pagado_val = monto_efectivo + monto_transferencia

        if monto_pagado_val > total:
            messages.error(request, 'El monto pagado no puede ser mayor al total de la venta.')
            return redirect('ventas')

        # Determine tipo_pago and estado
        if monto_pagado_val >= total:
            tipo_pago = 'completo'
            monto_pagado_val = total
            monto_efectivo = min(monto_efectivo, total)
            monto_transferencia = total - monto_efectivo
            fecha_vencimiento = None
            estado_pago = 'pagado'
        else:
            tipo_pago = 'fiado'
            try:
                dias_credito = int(dias_credito)
            except ValueError:
                dias_credito = 15
            fecha_vencimiento = timezone.localdate() + timedelta(days=dias_credito)
            estado_pago = 'pendiente'

        # Determine metodo_pago from amounts
        tiene_credito = tipo_pago == 'fiado'
        tiene_efectivo = monto_efectivo > 0
        tiene_transferencia = monto_transferencia > 0
        if tiene_credito:
            if tiene_efectivo and tiene_transferencia:
                metodo_pago = 'mixto_fiado'
            elif tiene_efectivo:
                metodo_pago = 'efectivo_fiado'
            elif tiene_transferencia:
                metodo_pago = 'transferencia_fiado'
            else:
                metodo_pago = 'fiado'
        else:
            if tiene_efectivo and tiene_transferencia:
                metodo_pago = 'mixto'
            elif tiene_transferencia:
                metodo_pago = 'transferencia'
            else:
                metodo_pago = 'efectivo'

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
            monto_efectivo=monto_efectivo,
            monto_transferencia=monto_transferencia,
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


@login_required
def detalle_venta(request, venta_id):
    """
    Muestra el detalle completo de una venta con opción de editar o agregar pagos.
    """
    venta = get_object_or_404(Venta, idVenta=venta_id)
    detalles = venta.detalles.select_related('producto').all()
    cobros = venta.cobros.all().order_by('-fecha')
    
    context = {
        'venta': venta,
        'detalles': detalles,
        'cobros': cobros,
    }
    
    return render(request, 'venta_detalle.html', context)


@login_required
def editar_venta(request, venta_id):
    """
    Permite editar una venta existente:
    - Restar cantidades de productos (en la tabla editable)
    - Agregar nuevos productos
    - Aumentar cantidades de productos existentes
    
    Al realizar cualquier cambio, recalcula automáticamente los totales.
    """
    venta = get_object_or_404(Venta, idVenta=venta_id)
    
    if request.method == 'POST':
        # Verificar si se están actualizando cantidades de la tabla
        cantidades_actualizadas = {key: value for key, value in request.POST.items() if key.startswith('cantidad_')}
        
        if cantidades_actualizadas:
            # Procesar actualización de cantidades (y precios) en la tabla
            try:
                with transaction.atomic():
                    cambios = False
                    for key, nueva_cantidad_str in cantidades_actualizadas.items():
                        try:
                            detalle_id = int(key.replace('cantidad_', ''))
                            nueva_cantidad = int(nueva_cantidad_str) or 0

                            detalle = DetalleVenta.objects.get(id=detalle_id, venta=venta)
                            cantidad_original = detalle.cantidad
                            precio_original = detalle.precio_venta

                            # Leer nuevo precio si viene en el POST
                            precio_key = f'precio_{detalle_id}'
                            nuevo_precio_str = request.POST.get(precio_key)
                            if nuevo_precio_str:
                                try:
                                    nuevo_precio = Decimal(str(int(float(nuevo_precio_str))))
                                    if nuevo_precio > 0:
                                        detalle.precio_venta = nuevo_precio
                                except (ValueError, Exception):
                                    pass

                            # Actualizar si cambió cantidad o precio
                            if nueva_cantidad != cantidad_original or detalle.precio_venta != precio_original:
                                detalle.cantidad = nueva_cantidad
                                detalle.subtotal = detalle.precio_venta * Decimal(str(nueva_cantidad))
                                detalle.ganancia = (detalle.precio_venta - detalle.precio_compra) * Decimal(str(nueva_cantidad))
                                detalle.save()
                                cambios = True

                                messages.info(
                                    request,
                                    f'{detalle.producto.nombre}: {nueva_cantidad} kg a ${detalle.precio_venta}/kg'
                                )
                        except (ValueError, DetalleVenta.DoesNotExist):
                            continue
                    
                    if cambios:
                        # Recalcular totales de la venta
                        recalcular_totales_venta(venta)
                        venta.actualizar_estado_pago()
                        messages.success(request, 'Cantidades actualizadas correctamente.')
                    else:
                        messages.info(request, 'No se realizaron cambios.')
                        
            except Exception as e:
                messages.error(request, f'Error al actualizar cantidades: {str(e)}')
            
            return redirect('detalle_venta', venta_id=venta_id)
        
        else:
            # Procesar formulario de agregar/aumentar productos
            form = EditarVentaForm(venta=venta, data=request.POST)
            if form.is_valid():
                accion = form.cleaned_data['accion']
                producto = form.cleaned_data['producto']
                cantidad = form.cleaned_data['cantidad']
                precio_venta = Decimal(str(form.cleaned_data['precio_venta']))
                
                try:
                    with transaction.atomic():
                        if accion == 'agregar_producto':
                            # Verificar que el producto no esté ya en la venta
                            existe = venta.detalles.filter(producto=producto).exists()
                            if existe:
                                messages.error(
                                    request,
                                    f'El producto {producto.nombre} ya está en esta venta. '
                                    'Use "Aumentar cantidad" para modificar la cantidad.'
                                )
                                return redirect('editar_venta', venta_id=venta_id)
                            
                            # Crear nuevo detalle
                            precio_compra = Decimal(str(producto.precio_compra))
                            subtotal = precio_venta * Decimal(str(cantidad))
                            ganancia = (precio_venta - precio_compra) * Decimal(str(cantidad))
                            
                            DetalleVenta.objects.create(
                                venta=venta,
                                producto=producto,
                                cantidad=cantidad,
                                precio_compra=precio_compra,
                                precio_venta=precio_venta,
                                subtotal=subtotal,
                                ganancia=ganancia,
                            )
                            
                            messages.success(
                                request,
                                f'Producto {producto.nombre} agregado: {cantidad} kg'
                            )
                        
                        elif accion == 'aumentar_cantidad':
                            # Obtener detalle existente
                            detalle = venta.detalles.get(producto=producto)
                            precio_compra = detalle.precio_compra
                            
                            # Recalcular con la nueva cantidad
                            nueva_cantidad = detalle.cantidad + cantidad
                            nuevo_subtotal = precio_venta * Decimal(str(nueva_cantidad))
                            nueva_ganancia = (precio_venta - precio_compra) * Decimal(str(nueva_cantidad))
                            
                            # Actualizar detalle
                            detalle.cantidad = nueva_cantidad
                            detalle.precio_venta = precio_venta
                            detalle.subtotal = nuevo_subtotal
                            detalle.ganancia = nueva_ganancia
                            detalle.save()
                            
                            messages.success(
                                request,
                                f'Cantidad de {producto.nombre} aumentada a {nueva_cantidad} kg'
                            )
                        
                        # Recalcular totales de la venta
                        recalcular_totales_venta(venta)
                        venta.actualizar_estado_pago()
                        
                except DetalleVenta.DoesNotExist:
                    messages.error(request, 'No se encontró el producto en la venta')
                except Exception as e:
                    messages.error(request, f'Error al actualizar la venta: {str(e)}')
                
                return redirect('detalle_venta', venta_id=venta_id)
    else:
        form = EditarVentaForm(venta=venta)
    
    detalles = venta.detalles.select_related('producto').all()
    
    context = {
        'venta': venta,
        'form': form,
        'detalles': detalles,
    }
    
    return render(request, 'venta_editar.html', context)


@login_required
def agregar_pago(request, venta_id):
    """
    Permite agregar un pago/abono a una venta a crédito.
    Recalcula automáticamente el estado de pago.
    """
    venta = get_object_or_404(Venta, idVenta=venta_id)
    
    # Validar que sea una venta a crédito
    if venta.tipo_pago != 'fiado':
        messages.error(request, 'Esta venta ya fue pagada completamente')
        return redirect('detalle_venta', venta_id=venta_id)
    
    # Validar que aún haya saldo pendiente
    if venta.saldo_pendiente <= 0:
        messages.info(request, 'Esta venta ya está completamente pagada')
        return redirect('detalle_venta', venta_id=venta_id)
    
    if request.method == 'POST':
        form = CobroForm(venta=venta, data=request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    monto = form.cleaned_data['monto']
                    
                    # Crear registro de cobro
                    Cobro.objects.create(
                        venta=venta,
                        monto=monto,
                    )
                    
                    # Actualizar monto_pagado en la venta
                    venta.monto_pagado += monto
                    venta.save()
                    
                    # Recalcular estado de pago
                    venta.actualizar_estado_pago()
                    
                    saldo = venta.saldo_pendiente
                    
                    if saldo <= 0:
                        messages.success(
                            request,
                            f'Abono registrado por ${monto:,.2f}. ¡Venta completamente pagada!'
                        )
                    else:
                        messages.success(
                            request,
                            f'Abono registrado por ${monto:,.2f}. Saldo pendiente: ${saldo:,.2f}'
                        )
                    
            except Exception as e:
                messages.error(request, f'Error al registrar el abono: {str(e)}')
            
            return redirect('detalle_venta', venta_id=venta_id)
    else:
        form = CobroForm(venta=venta)
    
    context = {
        'venta': venta,
        'form': form,
        'saldo_pendiente': venta.saldo_pendiente,
    }
    
    return render(request, 'venta_pago.html', context)


@login_required
def eliminar_detalle(request, venta_id, detalle_id):
    """
    Permite eliminar un producto de la venta (solo para ventas sin pagar).
    Recalcula totales automáticamente.
    """
    venta = get_object_or_404(Venta, idVenta=venta_id)
    detalle = get_object_or_404(DetalleVenta, id=detalle_id, venta=venta)
    
    # Validación: No permitir eliminar si ya hay pagos parciales
    if venta.monto_pagado > 0 and venta.tipo_pago == 'fiado':
        messages.error(
            request,
            'No puede modificar productos de una venta que ya tiene pagos registrados'
        )
        return redirect('detalle_venta', venta_id=venta_id)
    
    try:
        with transaction.atomic():
            producto_nombre = detalle.producto.nombre
            detalle.delete()
            
            # Recalcular totales
            recalcular_totales_venta(venta)
            
            # Si no quedan detalles, no se puede mantener la venta abierta
            if not venta.detalles.exists():
                messages.warning(request, 'La venta no tiene productos. Puede eliminarla.')
            else:
                messages.success(request, f'Producto {producto_nombre} eliminado')
            
    except Exception as e:
        messages.error(request, f'Error al eliminar el producto: {str(e)}')
    
    return redirect('editar_venta', venta_id=venta_id)


# ============================================================================
# FUNCIONES AUXILIARES (UTILIDADES)
# ============================================================================

def recalcular_totales_venta(venta):
    """
    Recalcula los totales de una venta basado en sus detalles (DetalleVenta).
    
    Esta función es crítica para mantener la consistencia de datos después
    de modificar productos en una venta. Se llama automáticamente cuando se:
    - Agregan productos
    - Aumentan cantidades
    - Eliminan productos
    
    Args:
        venta (Venta): La instancia de venta a recalcular
    """
    detalles = venta.detalles.all()
    
    if not detalles.exists():
        # Si no hay detalles, poner todo en 0
        venta.cantidad = 0
        venta.total = Decimal('0')
        venta.ganancia = Decimal('0')
    else:
        # Sumar todos los detalles usando agregación de ORM
        agregados = detalles.aggregate(
            total_cantidad=Sum('cantidad'),
            total_venta=Sum('subtotal'),
            total_ganancia=Sum('ganancia')
        )
        
        venta.cantidad = agregados['total_cantidad'] or 0
        venta.total = agregados['total_venta'] or Decimal('0')
        venta.ganancia = agregados['total_ganancia'] or Decimal('0')
        
        # Si es venta única, actualizar precio_compra y precio_venta
        if detalles.count() == 1:
            detalle = detalles.first()
            venta.precio_compra = detalle.precio_compra
            venta.precio_venta = detalle.precio_venta
            venta.producto = detalle.producto
        else:
            # Para múltiples productos, dejar los promedios
            venta.producto = None
            total_cantidad = venta.cantidad
            if total_cantidad > 0:
                venta.precio_compra = detalles.aggregate(
                    avg=Sum('precio_compra') / total_cantidad
                )['avg'] or Decimal('0')
                venta.precio_venta = detalles.aggregate(
                    avg=Sum('subtotal') / total_cantidad
                )['avg'] or Decimal('0')
    
    venta.save()


@login_required
@require_POST
def actualizar_detalle_venta(request, venta_id, detalle_id):
    """
    Actualiza la cantidad de un detalle de venta via AJAX.
    Recalcula automáticamente subtotales y ganancias.
    
    Esperado en el request.body: JSON con { "cantidad": numero }
    """
    venta = get_object_or_404(Venta, idVenta=venta_id)
    detalle = get_object_or_404(DetalleVenta, id=detalle_id, venta=venta)
    
    try:
        data = json.loads(request.body)
        nueva_cantidad = int(data.get('cantidad', 0))
        
        # Validación
        if nueva_cantidad < 0:
            return JsonResponse({'success': False, 'error': 'La cantidad no puede ser negativa'})
        
        if nueva_cantidad == 0:
            # Eliminar el detalle
            detalle.delete()
            recalcular_totales_venta(venta)
            return JsonResponse({'success': True, 'eliminado': True})
        
        # Actualizar cantidad
        detalle.cantidad = nueva_cantidad
        detalle.subtotal = detalle.precio_venta * Decimal(str(nueva_cantidad))
        detalle.ganancia = (detalle.precio_venta - detalle.precio_compra) * Decimal(str(nueva_cantidad))
        detalle.save()
        
        # Recalcular totales de la venta
        recalcular_totales_venta(venta)
        venta.actualizar_estado_pago()
        
        return JsonResponse({
            'success': True,
            'nuevo_subtotal': float(detalle.subtotal),
            'nueva_ganancia': float(detalle.ganancia),
            'total_venta': float(venta.total),
            'ganancia_venta': float(venta.ganancia),
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'La cantidad debe ser un número'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})


@login_required
@require_POST
def eliminar_detalle_venta(request, venta_id, detalle_id):
    """
    Elimina un producto de una venta via AJAX.
    Recalcula automáticamente los totales.
    """
    venta = get_object_or_404(Venta, idVenta=venta_id)
    detalle = get_object_or_404(DetalleVenta, id=detalle_id, venta=venta)
    
    try:
        producto_nombre = detalle.producto.nombre
        detalle.delete()
        
        # Recalcular totales
        recalcular_totales_venta(venta)
        venta.actualizar_estado_pago()
        
        # Si no quedan detalles, la venta queda sin productos
        if not venta.detalles.exists():
            return JsonResponse({
                'success': True,
                'mensaje': f'Producto {producto_nombre} eliminado. La venta no tiene productos.',
                'venta_vacia': True
            })
        else:
            return JsonResponse({
                'success': True,
                'mensaje': f'Producto {producto_nombre} eliminado',
                'total_venta': float(venta.total),
                'ganancia_venta': float(venta.ganancia),
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})

