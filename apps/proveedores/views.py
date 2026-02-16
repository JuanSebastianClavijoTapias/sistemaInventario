from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.

from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView
from django.db.models import Sum
from .models import Proveedores
from apps.productos.models import Productos


class ProveedorListView(ListView):
    model = Proveedores
    template_name = 'proveedores.html'
    context_object_name = 'proveedores'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_proveedores'] = Proveedores.objects.count()
        context['total_por_pagar'] = Proveedores.objects.aggregate(Sum('saldo'))['saldo__sum'] or 0
        context['total_pagado'] = Proveedores.objects.aggregate(Sum('inicial'))['inicial__sum'] or 0
        return context

    def post(self, request, *args, **kwargs):
        nombre = request.POST.get('proveedorNombre')
        telefono = request.POST.get('proveedorTelefono')
        descripcion = request.POST.get('proveedorDescripcion')
        cantidad = request.POST.get('proveedorCantidad')
        compra = request.POST.get('proveedorCompra')
        inicial = request.POST.get('proveedorInicial')
        tipo = request.POST.get('proveedorTipo')
        
        if not nombre or not telefono or not cantidad or not compra or not tipo:
            messages.error(request, 'Todos los campos obligatorios deben ser completados.')
            return redirect('proveedores')
        
        if tipo == 'fiada' and not inicial:
            messages.error(request, 'Para compra fiada, el pago inicial es obligatorio.')
            return redirect('proveedores')
        
        try:
            cantidad = int(float(cantidad))
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número entero válido.')
            return redirect('proveedores')
        
        try:
            compra = float(compra)
        except ValueError:
            messages.error(request, 'El monto total de compra debe ser un número válido.')
            return redirect('proveedores')
        
        if tipo == 'fiada':
            try:
                inicial = float(inicial) if inicial else 0
            except ValueError:
                messages.error(request, 'El pago inicial debe ser un número válido.')
                return redirect('proveedores')
        
        if tipo == 'completa':
            inicial = compra  # Para pago completo, inicial es igual al total
            saldo = 0
        elif tipo == 'fiada':
            inicial = float(inicial) if inicial else 0
            if inicial >= compra:
                messages.error(request, 'Para compra fiada, el pago inicial debe ser menor al monto total de compra.')
                return redirect('proveedores')
            saldo = compra - inicial
        else:
            messages.error(request, 'Tipo de compra inválido.')
            return redirect('proveedores')
        
        proveedor = Proveedores.objects.create(
            nombre=nombre,
            telefono=telefono,
            inicial=inicial,
            saldo=saldo
        )
        
        # Actualizar inventario
        if descripcion and cantidad > 0:
            precio_unit = compra / cantidad if cantidad > 0 else 0
            producto, created = Productos.objects.get_or_create(
                nombre=descripcion,
                proveedor=proveedor,
                defaults={'precio': precio_unit, 'stock': cantidad}
            )
            if not created:
                producto.stock += cantidad
                producto.save()
        
        messages.success(request, 'Proveedor y compra registrados exitosamente.')
        return redirect('proveedores')

class ProveedorUpdateView(UpdateView):
    model = Proveedores
    fields = ['nombre', 'telefono', 'inicial', 'saldo']
    template_name = 'proveedores_form.html'
    success_url = reverse_lazy('proveedores')

class ProveedorDeleteView(DeleteView):
    model = Proveedores
    template_name = 'proveedores_confirm_delete.html'
    success_url = reverse_lazy('proveedores')
