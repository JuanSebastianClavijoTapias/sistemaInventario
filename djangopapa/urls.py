"""
URL configuration for djangopapa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from panelprincipal import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cuenta-suspendida/', views.cuenta_suspendida, name='cuenta_suspendida'),
    path('', views.saludo, name='inicio'),
    path('liquidar/', views.liquidar_semana, name='liquidar_semana'),
    path('historial-semanas/', views.historial_semanas, name='historial_semanas'),
    path('historial-semanas/<int:pk>/', views.detalle_semana, name='detalle_semana'),
    path('ventas/', include('apps.ventas.urls')),
    path('productos/', include('apps.productos.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('proveedores/', include('apps.proveedores.urls')),
    path('gastos/', include('apps.gastos.urls')),
]

print("URLs loaded")  # Debug
