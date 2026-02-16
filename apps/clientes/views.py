from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

# Create your views here.

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.db.models import Sum
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
