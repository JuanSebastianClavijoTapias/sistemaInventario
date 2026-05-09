from django.urls import path
from apps.auditoria import views

app_name = 'auditoria'

urlpatterns = [
    path('historial/', views.historial_auditoria, name='historial'),
    path('api/historial-json/', views.ultimosRegistros, name='api_historial_json'),
    path('ultimos-registros/', views.ultimosRegistros, name='ultimos_registros'),
    path('resumen/', views.resumenAuditoria, name='resumen'),
    path('detalles/<int:registro_id>/', views.detalles_registro, name='detalles'),
]
