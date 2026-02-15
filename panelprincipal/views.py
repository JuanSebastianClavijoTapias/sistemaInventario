from django.shortcuts import render
from apps.clientes.models import Clientes
from apps.proveedores.models import Proveedores
from apps.productos.models import Productos
from apps.ventas.models import Venta
from apps.gastos.models import Gastos

# Create your views here.
def saludo(request):
    context = {
        'total_clientes': Clientes.objects.count(),
        'total_proveedores': Proveedores.objects.count(),
        'total_productos': Productos.objects.count(),
        'total_ventas': Venta.objects.count(),
        'total_gastos': Gastos.objects.count(),
    }
    print("Vista ejecutada, total_clientes:", context['total_clientes'])  # Temporal
    return render(request, 'index.html', context)

def ventas(request):
    return render(request, 'ventas.html')

def clientes(request):
    return render(request, 'clientes.html')

def proveedores(request):
    return render(request, 'proveedores.html')

def gastos(request):
    return render(request, 'gastos.html')