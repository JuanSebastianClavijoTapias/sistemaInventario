from django.shortcuts import render, redirect

# Create your views here.

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from .models import Clientes
from .forms import ClienteForm


class ClienteListView(FormMixin, ListView):
    model = Clientes
    template_name = 'clientes.html'
    context_object_name = 'clientes'
    form_class = ClienteForm
    success_url = reverse_lazy('cliente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
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
