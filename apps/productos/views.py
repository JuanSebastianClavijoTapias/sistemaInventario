from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib import messages
from .models import Productos
from apps.proveedores.models import Proveedores
from .forms import ProductoForm


class ProductoListView(ListView):
    model = Productos
    template_name = 'productos.html'
    context_object_name = 'productos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proveedores'] = Proveedores.objects.all()
        return context


class ProductoUpdateView(UpdateView):
    model = Productos
    fields = ['nombre', 'precio_compra', 'precio_venta', 'stock', 'proveedor']
    template_name = 'productos_form.html'
    success_url = reverse_lazy('productos')


class ProductoDeleteView(DeleteView):
    model = Productos
    template_name = 'productos_confirm_delete.html'
    success_url = reverse_lazy('productos')
