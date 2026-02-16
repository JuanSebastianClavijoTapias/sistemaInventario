from django.urls import path
from . import views

urlpatterns = [
    path('', views.trabajadores_list, name='trabajadores_list'),
    path('crear/', views.trabajadores_crear, name='trabajadores_crear'),
    path('editar/<int:id_trabajador>/', views.trabajadores_editar, name='trabajadores_editar'),
    path('eliminar/<int:id_trabajador>/', views.trabajadores_eliminar, name='trabajadores_eliminar'),
]