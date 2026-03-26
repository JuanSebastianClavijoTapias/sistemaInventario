from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal

# Create your views here.

from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView
from django.db.models import Sum
from .models import Proveedores
from apps.productos.models import Productos, CATEGORIA_CHOICES
from apps.gastos.models import Gastos


class ProveedorListView(ListView):
    model = Proveedores
    template_name = 'proveedores.html'
    context_object_name = 'proveedores'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_proveedores'] = Proveedores.objects.count()
        context['total_por_pagar'] = Proveedores.objects.aggregate(Sum('saldo'))['saldo__sum'] or 0
        context['total_pagado'] = Proveedores.objects.aggregate(Sum('inicial'))['inicial__sum'] or 0
        context['categoria_choices'] = CATEGORIA_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        nombre = request.POST.get('proveedorNombre')
        telefono = request.POST.get('proveedorTelefono')
        tipo = request.POST.get('proveedorTipo')
        inicial = request.POST.get('proveedorInicial')
        total_bultos_str = request.POST.get('totalBultos')
        precio_unitario_str = request.POST.get('precioUnitario')

        # Classification data
        categorias = request.POST.getlist('categoria[]')
        cantidades = request.POST.getlist('cantidad[]')

        if not nombre or not telefono or not tipo:
            messages.error(request, 'Todos los campos obligatorios deben ser completados.')
            return redirect('proveedores')

        try:
            total_bultos = int(float(total_bultos_str))
            precio_unitario = float(precio_unitario_str)
        except (ValueError, TypeError):
            messages.error(request, 'Los bultos totales y el precio unitario son obligatorios.')
            return redirect('proveedores')

        if total_bultos <= 0 or precio_unitario <= 0:
            messages.error(request, 'Los bultos y el precio deben ser mayores a cero.')
            return redirect('proveedores')

        total_compra = total_bultos * precio_unitario

        # Process classification items
        items = []
        cat_display_map = dict(CATEGORIA_CHOICES)
        suma_clasificados = 0

        for i in range(len(categorias)):
            if not categorias[i] or not cantidades[i]:
                continue
            try:
                cant = int(float(cantidades[i]))
            except (ValueError, IndexError):
                continue
            if cant <= 0:
                continue

            suma_clasificados += cant
            items.append({
                'categoria': categorias[i],
                'nombre': cat_display_map.get(categorias[i], categorias[i]),
                'cantidad': cant,
            })

        if not items:
            messages.error(request, 'Debe clasificar al menos una categoría.')
            return redirect('proveedores')

        if suma_clasificados > total_bultos:
            messages.error(request, f'Los bultos clasificados ({suma_clasificados}) superan el total comprado ({total_bultos}).')
            return redirect('proveedores')

        # Process payment type
        if tipo == 'completa':
            inicial_val = total_compra
            saldo = 0
        elif tipo == 'fiada':
            if not inicial:
                messages.error(request, 'Para compra fiada, el pago inicial es obligatorio.')
                return redirect('proveedores')
            try:
                inicial_val = float(inicial)
            except ValueError:
                messages.error(request, 'El pago inicial debe ser un número válido.')
                return redirect('proveedores')
            if inicial_val >= total_compra:
                messages.error(request, 'Para compra fiada, el pago inicial debe ser menor al monto total.')
                return redirect('proveedores')
            saldo = total_compra - inicial_val
        else:
            messages.error(request, 'Tipo de compra inválido.')
            return redirect('proveedores')

        # Create proveedor
        proveedor = Proveedores.objects.create(
            nombre=nombre,
            telefono=telefono,
            inicial=inicial_val,
            saldo=saldo
        )

        # Registrar el pago inicial como gasto
        if inicial_val > 0:
            Gastos.objects.create(
                descripcion=f'Compra a proveedor: {nombre}',
                monto=inicial_val,
                categoria='comercio_productos',
                proveedor=proveedor
            )

        # Create products for each classification (precio_venta=0, se define en la venta)
        for item in items:
            producto, created = Productos.objects.get_or_create(
                categoria=item['categoria'],
                proveedor=proveedor,
                defaults={
                    'nombre': item['nombre'],
                    'precio_compra': precio_unitario,
                    'precio_venta': 0,
                    'stock': item['cantidad']
                }
            )
            if not created:
                producto.stock += item['cantidad']
                producto.precio_compra = precio_unitario
                producto.save()
        
        # Check if there are unclassified bultos
        sin_clasificar = total_bultos - suma_clasificados
        if sin_clasificar > 0:
            messages.warning(request, f'Compra registrada. {sin_clasificar} bulto(s) quedaron sin clasificar.')
        else:
            messages.success(request, 'Proveedor y compra registrados exitosamente.')
        return redirect('proveedores')

class ProveedorUpdateView(UpdateView):
    model = Proveedores
    fields = ['nombre', 'telefono', 'inicial', 'saldo']
    template_name = 'proveedores_form.html'
    success_url = reverse_lazy('proveedores')

    def form_valid(self, form):
        proveedor_anterior = Proveedores.objects.get(pk=self.object.pk)
        saldo_anterior = proveedor_anterior.saldo
        saldo_nuevo = form.cleaned_data['saldo']
        
        # Si el saldo disminuyó, se hizo un pago → registrar como gasto
        if saldo_nuevo < saldo_anterior:
            monto_pagado = saldo_anterior - saldo_nuevo
            Gastos.objects.create(
                descripcion=f'Pago a proveedor: {self.object.nombre}',
                monto=monto_pagado,
                categoria='comercio_productos',
                proveedor=self.object
            )
        
        return super().form_valid(form)

class ProveedorDeleteView(DeleteView):
    model = Proveedores
    template_name = 'proveedores_confirm_delete.html'
    success_url = reverse_lazy('proveedores')


def pagar_proveedor(request, pk):
    """Registra un pago (abono o saldar) a un proveedor"""
    proveedor = get_object_or_404(Proveedores, pk=pk)
    
    if request.method == 'POST':
        monto_str = request.POST.get('monto_pago', '')
        saldar = request.POST.get('saldar') == '1'
        
        if saldar:
            monto = proveedor.saldo
        else:
            try:
                monto = Decimal(monto_str)
            except Exception:
                messages.error(request, 'El monto debe ser un número válido.')
                return redirect('proveedores')
        
        if monto <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('proveedores')
        
        if monto > proveedor.saldo:
            messages.error(request, f'El monto no puede ser mayor al saldo pendiente (${proveedor.saldo}).')
            return redirect('proveedores')
        
        # Reducir saldo del proveedor
        proveedor.saldo -= monto
        proveedor.inicial += monto
        proveedor.save()
        
        # Registrar como gasto
        Gastos.objects.create(
            descripcion=f'Pago a proveedor: {proveedor.nombre}',
            monto=monto,
            categoria='comercio_productos',
            proveedor=proveedor
        )
        
        if proveedor.saldo == 0:
            messages.success(request, f'Proveedor {proveedor.nombre} saldado completamente.')
        else:
            messages.success(request, f'Abono de ${monto} registrado. Saldo pendiente: ${proveedor.saldo}')
    
    return redirect('proveedores')
