from django.urls import path
from . import views

urlpatterns = [
    path('', views.ventas_form, name='ventas'),
]