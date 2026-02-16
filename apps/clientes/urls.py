from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClienteListView.as_view(), name='cliente_list'),
    path('<int:pk>/update/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('<int:pk>/delete/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    path('<int:pk>/compras/', views.cliente_compras, name='cliente_compras'),
    path('<int:pk>/compras/json/', views.cliente_compras_json, name='cliente_compras_json'),
    path('<int:pk>/pagar/', views.registrar_pago, name='registrar_pago'),
]