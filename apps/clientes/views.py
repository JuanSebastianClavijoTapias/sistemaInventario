from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages

# Create your views here.

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.db.models import Sum, F, Count, Q
from decimal import Decimal
from .models import Clientes
from .forms import ClienteForm
from apps.ventas.models import Venta


class ClienteListView(FormMixin, ListView):
    model = Clientes
    template_name = 'clientes.html'
    context_object_name = 'clientes'
    form_class = ClienteForm
    success_url = reverse_lazy('cliente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        
        # Clientes con deudas pendientes
        clientes_con_deuda = []
        clientes_pagados = []
        
        for cliente in context['clientes']:
            # Verificar si el cliente tiene ventas pendientes
            ventas_pendientes = Venta.objects.filter(
                cliente=cliente,
                estado_pago__in=['pendiente', 'vencido']
            )
            
            if ventas_pendientes.exists():
                total_deuda = sum(venta.saldo_pendiente for venta in ventas_pendientes)
                dias_vencimiento = []
                
                for venta in ventas_pendientes:
                    if venta.fecha_vencimiento:
                        dias = venta.dias_para_vencimiento
                        if dias is not None:
                            dias_vencimiento.append(dias)
                
                # Determinar el estado más crítico
                estado_critico = 'pendiente'
                dias_validos = [d for d in dias_vencimiento if d is not None]
                if any(d < 0 for d in dias_validos):
                    estado_critico = 'vencido'
                elif any(d <= 1 for d in dias_validos):
                    estado_critico = 'urgente'
                
                clientes_con_deuda.append({
                    'cliente': cliente,
                    'total_deuda': total_deuda,
                    'ventas_pendientes': ventas_pendientes.count(),
                    'estado': estado_critico,
                    'dias_minimos': min(d for d in dias_vencimiento if d is not None) if dias_vencimiento else None
                })
            else:
                # Cliente sin deudas
                total_compras = Venta.objects.filter(cliente=cliente).aggregate(
                    total=Sum('total')
                )['total'] or 0
                clientes_pagados.append({
                    'cliente': cliente,
                    'total_compras': total_compras
                })
        
        # Ordenar por deuda más alta primero
        clientes_con_deuda.sort(key=lambda x: x['total_deuda'], reverse=True)
        
        context['clientes_con_deuda'] = clientes_con_deuda
        context['clientes_pagados'] = clientes_pagados
        
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            form.save()
            return redirect('cliente_list')
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ClienteCreateView(CreateView):
    model = Clientes
    fields = ['nombre', 'apellido', 'telefono']
    template_name = 'clientes.html'
    success_url = reverse_lazy('cliente_list')

class ClienteUpdateView(UpdateView):
    model = Clientes
    fields = ['nombre', 'apellido', 'telefono']
    template_name = 'clientes_form.html'
    success_url = reverse_lazy('cliente_list')

class ClienteDeleteView(DeleteView):
    model = Clientes
    template_name = 'clientes_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')


def cliente_compras(request, pk):
    cliente = get_object_or_404(Clientes, idCliente=pk)
    compras = Venta.objects.filter(cliente=cliente).order_by('-fecha')
    total_compras = sum(venta.total for venta in compras)
    
    context = {
        'cliente': cliente,
        'compras': compras,
        'total_compras': total_compras,
    }
    return render(request, 'cliente_compras.html', context)


def cliente_compras_json(request, pk):
    cliente = get_object_or_404(Clientes, idCliente=pk)
    compras = Venta.objects.filter(cliente=cliente).order_by('-fecha')
    
    data = {
        'cliente': {
            'nombre': f"{cliente.nombre} {cliente.apellido}",
            'telefono': cliente.telefono,
        },
        'compras': [
            {
                'producto': venta.producto.nombre,
                'cantidad': venta.cantidad,
                'total': float(venta.total),
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
            }
            for venta in compras
        ],
        'total_compras': float(sum(venta.total for venta in compras)),
    }
    return JsonResponse(data)


def clientes_por_cobrar(request):
    """Vista que muestra todos los clientes con saldo pendiente por cobrar"""
    from django.db.models import F, Q
    
    # Clientes que tienen al menos una venta pendiente/vencida
    clientes_deudores = Clientes.objects.filter(
        ventas__estado_pago__in=['pendiente', 'vencido']
    ).distinct().annotate(
        total_deuda=Sum(
            F('ventas__total') - F('ventas__monto_pagado'),
            filter=Q(ventas__estado_pago__in=['pendiente', 'vencido'])
        ),
        cantidad_ventas_pendientes=Count(
            'ventas',
            filter=Q(ventas__estado_pago__in=['pendiente', 'vencido'])
        ),
    ).order_by('-total_deuda')
    
    # Total global
    total_por_cobrar = Venta.objects.filter(
        estado_pago__in=['pendiente', 'vencido']
    ).aggregate(
        total=Sum(F('total') - F('monto_pagado'))
    )['total'] or 0
    
    total_clientes_deudores = clientes_deudores.count()
    
    # Para cada cliente, sus ventas pendientes
    clientes_con_ventas = []
    for cliente in clientes_deudores:
        ventas_pendientes = Venta.objects.filter(
            cliente=cliente,
            estado_pago__in=['pendiente', 'vencido']
        ).select_related('producto').order_by('fecha_vencimiento')
        clientes_con_ventas.append({
            'cliente': cliente,
            'ventas': ventas_pendientes,
            'total_deuda': cliente.total_deuda,
            'cantidad_ventas': cliente.cantidad_ventas_pendientes,
        })
    
    context = {
        'clientes_con_ventas': clientes_con_ventas,
        'total_por_cobrar': total_por_cobrar,
        'total_clientes_deudores': total_clientes_deudores,
    }
    return render(request, 'clientes_por_cobrar.html', context)


def saldar_venta(request, pk):
    """Salda completamente una venta (marca como pagada)"""
    venta = get_object_or_404(Venta, idVenta=pk)
    
    if request.method == 'POST':
        if venta.estado_pago == 'pagado':
            messages.warning(request, 'Esta venta ya está completamente pagada.')
        else:
            # Saldar completamente
            venta.monto_pagado = venta.total
            venta.estado_pago = 'pagado'
            venta.save()
            messages.success(request, f'Venta #{venta.idVenta} saldada exitosamente. Cliente: {venta.cliente}')
    
    return redirect('clientes_por_cobrar')


def pago_parcial_cobrar(request):
    """Registra un pago parcial desde la vista de clientes por cobrar"""
    if request.method == 'POST':
        venta_id = request.POST.get('venta_id')
        monto_pago = request.POST.get('monto_pago')
        
        if not venta_id or not monto_pago:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('clientes_por_cobrar')
        
        try:
            monto_pago = Decimal(monto_pago)
        except (ValueError, TypeError):
            messages.error(request, 'El monto debe ser un número válido.')
            return redirect('clientes_por_cobrar')
        
        try:
            venta = Venta.objects.get(idVenta=venta_id)
        except Venta.DoesNotExist:
            messages.error(request, 'Venta no encontrada.')
            return redirect('clientes_por_cobrar')
        
        if venta.estado_pago == 'pagado':
            messages.error(request, 'Esta venta ya está completamente pagada.')
            return redirect('clientes_por_cobrar')
        
        if monto_pago > venta.saldo_pendiente:
            messages.error(request, f'El monto no puede ser mayor al saldo pendiente (${venta.saldo_pendiente}).')
            return redirect('clientes_por_cobrar')
        
        if monto_pago <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('clientes_por_cobrar')
        
        # Actualizar el monto pagado
        venta.monto_pagado += monto_pago
        venta.actualizar_estado_pago()
        venta.save()
        
        messages.success(request, f'Abono de ${monto_pago} registrado. Saldo pendiente: ${venta.saldo_pendiente}')
    
    return redirect('clientes_por_cobrar')


def registrar_pago(request, pk):
    cliente = get_object_or_404(Clientes, idCliente=pk)
    
    if request.method == 'POST':
        venta_id = request.POST.get('venta_id')
        monto_pago = request.POST.get('monto_pago')
        
        if not venta_id or not monto_pago:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('cliente_compras', pk=cliente.pk)
        
        try:
            monto_pago = Decimal(monto_pago)
        except (ValueError, TypeError):
            messages.error(request, 'El monto debe ser un número válido.')
            return redirect('cliente_compras', pk=cliente.pk)
        
        try:
            venta = Venta.objects.get(idVenta=venta_id, cliente=cliente)
        except Venta.DoesNotExist:
            messages.error(request, 'Venta no encontrada.')
            return redirect('cliente_compras', pk=cliente.pk)
        
        if venta.estado_pago == 'pagado':
            messages.error(request, 'Esta venta ya está completamente pagada.')
            return redirect('cliente_compras', pk=cliente.pk)
        
        if monto_pago > venta.saldo_pendiente:
            messages.error(request, f'El monto no puede ser mayor al saldo pendiente (${venta.saldo_pendiente}).')
            return redirect('cliente_compras', pk=cliente.pk)
        
        # Actualizar el monto pagado
        venta.monto_pagado += monto_pago
        venta.actualizar_estado_pago()
        venta.save()
        
        messages.success(request, f'Pago registrado exitosamente. Saldo pendiente: ${venta.saldo_pendiente}')
        return redirect('cliente_compras', pk=cliente.pk)
    
    # Si no es POST, redirigir a la vista de compras
    return redirect('cliente_compras', pk=cliente.pk)
