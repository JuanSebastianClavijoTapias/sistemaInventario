from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.contrib import messages
from .models import Productos
from apps.proveedores.models import Proveedores
from .forms import ProductoForm


class ProductoListView(FormMixin, ListView):
    model = Productos
    template_name = 'productos.html'
    context_object_name = 'productos'
    form_class = ProductoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['proveedores'] = Proveedores.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado exitosamente.')
            return redirect('productos')
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ProductoUpdateView(UpdateView):
    model = Productos
    fields = ['nombre', 'precio', 'stock', 'proveedor']
    template_name = 'productos_form.html'
    success_url = reverse_lazy('productos')


class ProductoDeleteView(DeleteView):
    model = Productos
    template_name = 'productos_confirm_delete.html'
    success_url = reverse_lazy('productos')
