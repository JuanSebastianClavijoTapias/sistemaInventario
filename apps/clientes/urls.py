from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClienteListView.as_view(), name='cliente_list'),
    path('<int:pk>/update/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('<int:pk>/delete/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
]