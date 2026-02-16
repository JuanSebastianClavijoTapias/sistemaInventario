from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProveedorListView.as_view(), name='proveedores'),
    path('<int:pk>/update/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('<int:pk>/delete/', views.ProveedorDeleteView.as_view(), name='proveedor_delete'),
]