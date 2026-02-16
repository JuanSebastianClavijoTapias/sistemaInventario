from django.urls import path
from . import views

urlpatterns = [
    path('', views.gastos_list, name='gastos'),
    path('crear/', views.gastos_crear, name='gastos_crear'),
    path('editar/<int:pk>/', views.gastos_editar, name='gastos_editar'),
    path('eliminar/<int:pk>/', views.gastos_eliminar, name='gastos_eliminar'),
]
