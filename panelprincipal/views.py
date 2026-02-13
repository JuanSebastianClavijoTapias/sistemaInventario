from django.shortcuts import render

# Create your views here.
def saludo(request):
    return render(request, 'index.html')

def ventas(request):
    return render(request, 'ventas.html')

def clientes(request):
    return render(request, 'clientes.html')

def proveedores(request):
    return render(request, 'proveedores.html')

def gastos(request):
    return render(request, 'gastos.html')