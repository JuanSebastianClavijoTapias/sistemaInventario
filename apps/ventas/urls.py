from django.urls import path
from . import views

urlpatterns = [
    # Venta principal
    path('', views.ventas_form, name='ventas'),
    
    # Gestión de ventas
    path('lista/', views.lista_ventas, name='lista_ventas'),
    path('<int:venta_id>/detalle/', views.detalle_venta, name='detalle_venta'),
    path('<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),
    
    # Pagos/abonos
    path('<int:venta_id>/pago/', views.agregar_pago, name='agregar_pago'),
    
    # Detalles
    path('<int:venta_id>/detalle/<int:detalle_id>/eliminar/', 
         views.eliminar_detalle, name='eliminar_detalle'),
]