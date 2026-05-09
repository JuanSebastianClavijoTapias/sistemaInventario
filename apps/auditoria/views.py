from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q, F, Value, CharField, Count
from django.db.models.functions import Concat
from django.core.paginator import Paginator
from apps.auditoria.models import RegistroAuditoria
from datetime import datetime, timedelta
import json


@login_required
def historial_auditoria(request):
    """
    Vista que muestra el historial de auditoría completo con filtros.
    """
    registros = RegistroAuditoria.objects.all()
    
    # Filtros
    accion = request.GET.get('accion')
    modelo = request.GET.get('modelo')
    usuario = request.GET.get('usuario')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    busqueda = request.GET.get('busqueda')
    
    # Aplicar filtros
    if accion and accion != 'todos':
        registros = registros.filter(accion=accion)
    
    if modelo and modelo != 'todos':
        registros = registros.filter(modelo=modelo)
    
    if usuario and usuario != '':
        registros = registros.filter(usuario__id=usuario)
    
    if fecha_desde:
        try:
            fecha = datetime.strptime(fecha_desde, '%Y-%m-%d')
            registros = registros.filter(fecha_hora__date__gte=fecha.date())
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            registros = registros.filter(fecha_hora__date__lte=fecha.date())
        except ValueError:
            pass
    
    if busqueda:
        registros = registros.filter(
            Q(descripcion_objeto__icontains=busqueda) |
            Q(detalles__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(registros, 20)
    pagina = request.GET.get('page', 1)
    registros_pagina = paginator.get_page(pagina)
    
    # Obtener opciones para filtros
    acciones = RegistroAuditoria.ACCIONES
    modelos = RegistroAuditoria.MODELOS_REGISTRADOS.items()
    
    # Obtener usuarios únicos con nombres
    from django.contrib.auth.models import User
    usuarios = User.objects.filter(registros_auditoria__isnull=False).annotate(
        nombre_completo=Concat(
            F('first_name'), Value(' '), F('last_name'),
            output_field=CharField()
        )
    ).values('id', 'nombre_completo', 'username').distinct()
    
    context = {
        'registros': registros_pagina,
        'acciones': acciones,
        'modelos': modelos,
        'usuarios': usuarios,
        'filtros': {
            'accion': accion,
            'modelo': modelo,
            'usuario': usuario,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'busqueda': busqueda,
        }
    }
    
    return render(request, 'auditoria/historial_auditoria.html', context)


@login_required
def ultimosRegistros(request):
    """
    API endpoint que retorna los últimos registros de auditoría.
    Usado para el dashboard.
    """
    limite = int(request.GET.get('limite', 10))
    modelo = request.GET.get('modelo')
    
    registros = RegistroAuditoria.objects.all().order_by('-fecha_hora')[:limite]
    
    if modelo:
        registros = RegistroAuditoria.objects.filter(modelo=modelo).order_by('-fecha_hora')[:limite]
    
    data = {
        'registros': [
            {
                'id': r.id,
                'accion': r.get_accion_display(),
                'usuario': (f"{r.usuario.first_name} {r.usuario.last_name}".strip() or r.usuario.username) if r.usuario else 'Sistema',
                'descripcion': r.obtener_resumen(),
                'fecha_hora': r.fecha_hora.strftime('%d/%m/%Y %H:%M:%S'),
                'modelo': r.modelo,
            }
            for r in registros
        ]
    }
    
    return JsonResponse(data)


@login_required
def resumenAuditoria(request):
    """
    Retorna un resumen de auditoría para mostrar en el dashboard.
    """
    hoy = datetime.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    
    # Estadísticas
    total_registros = RegistroAuditoria.objects.count()
    registros_hoy = RegistroAuditoria.objects.filter(
        fecha_hora__date=hoy
    ).count()
    registros_semana = RegistroAuditoria.objects.filter(
        fecha_hora__date__gte=hace_7_dias
    ).count()
    
    # Por acción
    por_accion = {}
    for accion, label in RegistroAuditoria.ACCIONES:
        por_accion[label] = RegistroAuditoria.objects.filter(accion=accion).count()
    
    # Por modelo
    por_modelo = {}
    for modelo_key, modelo_label in RegistroAuditoria.MODELOS_REGISTRADOS.items():
        por_modelo[modelo_label] = RegistroAuditoria.objects.filter(modelo=modelo_key).count()
    
    # Por usuario (top 5)
    usuarios_top = RegistroAuditoria.objects.annotate(
        usuario_nombre=Concat(
            F('usuario__first_name'), Value(' '), F('usuario__last_name'),
            output_field=CharField()
        )
    ).values(
        'usuario__username', 'usuario_nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    data = {
        'total_registros': total_registros,
        'registros_hoy': registros_hoy,
        'registros_semana': registros_semana,
        'por_accion': por_accion,
        'por_modelo': por_modelo,
        'usuarios_top': list(usuarios_top),
    }
    
    return JsonResponse(data)


@login_required
def detalles_registro(request, registro_id):
    """
    Retorna los detalles completos de un registro de auditoría.
    """
    try:
        registro = RegistroAuditoria.objects.get(id=registro_id)
        
        usuario_nombre = 'Sistema'
        if registro.usuario:
            nombre = f"{registro.usuario.first_name} {registro.usuario.last_name}".strip()
            usuario_nombre = nombre if nombre else registro.usuario.username
        
        data = {
            'id': registro.id,
            'accion': registro.get_accion_display(),
            'usuario': usuario_nombre,
            'fecha_hora': registro.fecha_hora.strftime('%d/%m/%Y %H:%M:%S'),
            'modelo': registro.modelo,
            'descripcion_objeto': registro.descripcion_objeto,
            'detalles': registro.detalles,
            'cambios': registro.obtener_cambios_legibles(),
            'valores_antes': registro.valores_antes,
            'valores_despues': registro.valores_despues,
        }
        
        return JsonResponse(data)
    except RegistroAuditoria.DoesNotExist:
        return JsonResponse({'error': 'Registro no encontrado'}, status=404)
