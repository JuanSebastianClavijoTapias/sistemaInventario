from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductoListView.as_view(), name='productos'),
    path('<int:pk>/update/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('<int:pk>/delete/', views.ProductoDeleteView.as_view(), name='producto_delete'),
]