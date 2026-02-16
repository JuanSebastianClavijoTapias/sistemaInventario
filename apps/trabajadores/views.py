from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import Trabajadores


def trabajadores_list(request):
    """Vista principal de trabajadores con listado y formulario."""
    trabajadores = Trabajadores.objects.all()

    # Calcular totales
    total_trabajadores = trabajadores.count()
    trabajadores_activos = trabajadores.filter(activo=True).count()
    total_salarios = trabajadores.filter(activo=True).aggregate(total=Sum('salario'))['total'] or 0

    # Trabajadores por cargo
    trabajadores_por_cargo = {}
    for cargo, nombre in Trabajadores.CARGO_CHOICES:
        cantidad = trabajadores.filter(cargo=cargo, activo=True).count()
        trabajadores_por_cargo[cargo] = {
            'nombre': nombre,
            'cantidad': cantidad
        }

    context = {
        'trabajadores': trabajadores,
        'total_trabajadores': total_trabajadores,
        'trabajadores_activos': trabajadores_activos,
        'total_salarios': total_salarios,
        'trabajadores_por_cargo': trabajadores_por_cargo,
        'cargos': Trabajadores.CARGO_CHOICES,
    }
    return render(request, 'trabajadores.html', context)


def trabajadores_crear(request):
    """Vista para crear un nuevo trabajador."""
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            telefono = request.POST.get('telefono')
            cargo = request.POST.get('cargo')
            salario = request.POST.get('salario')
            fecha_ingreso = request.POST.get('fecha_ingreso')

            # Validar datos
            if not nombre or not apellido:
                messages.error(request, 'Nombre y apellido son obligatorios.')
                return redirect('trabajadores_form')

            try:
                salario = Decimal(salario) if salario else 0
            except (InvalidOperation, ValueError):
                messages.error(request, 'El salario debe ser un número válido.')
                return redirect('trabajadores_form')

            # Crear trabajador
            Trabajadores.objects.create(
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
                cargo=cargo,
                salario=salario,
                fecha_ingreso=fecha_ingreso if fecha_ingreso else timezone.now().date()
            )

            messages.success(request, f'Trabajador {nombre} {apellido} creado exitosamente.')
            return redirect('trabajadores_list')

        except Exception as e:
            messages.error(request, f'Error al crear el trabajador: {str(e)}')
            return redirect('trabajadores_form')

    # GET request - mostrar formulario vacío
    context = {
        'cargos': Trabajadores.CARGO_CHOICES,
    }
    return render(request, 'trabajadores_form.html', context)


def trabajadores_editar(request, id_trabajador):
    """Vista para editar un trabajador existente."""
    trabajador = get_object_or_404(Trabajadores, idTrabajador=id_trabajador)

    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            telefono = request.POST.get('telefono')
            cargo = request.POST.get('cargo')
            salario = request.POST.get('salario')
            fecha_ingreso = request.POST.get('fecha_ingreso')
            activo = request.POST.get('activo') == 'on'

            # Validar datos
            if not nombre or not apellido:
                messages.error(request, 'Nombre y apellido son obligatorios.')
                return redirect('trabajadores_editar', id_trabajador=id_trabajador)

            try:
                salario = Decimal(salario) if salario else 0
            except (InvalidOperation, ValueError):
                messages.error(request, 'El salario debe ser un número válido.')
                return redirect('trabajadores_editar', id_trabajador=id_trabajador)

            # Actualizar trabajador
            trabajador.nombre = nombre
            trabajador.apellido = apellido
            trabajador.telefono = telefono
            trabajador.cargo = cargo
            trabajador.salario = salario
            trabajador.fecha_ingreso = fecha_ingreso if fecha_ingreso else trabajador.fecha_ingreso
            trabajador.activo = activo
            trabajador.save()

            messages.success(request, f'Trabajador {nombre} {apellido} actualizado exitosamente.')
            return redirect('trabajadores_list')

        except Exception as e:
            messages.error(request, f'Error al actualizar el trabajador: {str(e)}')
            return redirect('trabajadores_editar', id_trabajador=id_trabajador)

    # GET request - mostrar formulario con datos del trabajador
    context = {
        'trabajador': trabajador,
        'cargos': Trabajadores.CARGO_CHOICES,
    }
    return render(request, 'trabajadores_form.html', context)


def trabajadores_eliminar(request, id_trabajador):
    """Vista para confirmar eliminación de un trabajador."""
    trabajador = get_object_or_404(Trabajadores, idTrabajador=id_trabajador)

    if request.method == 'POST':
        try:
            nombre_completo = f"{trabajador.nombre} {trabajador.apellido}"
            trabajador.delete()
            messages.success(request, f'Trabajador {nombre_completo} eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el trabajador: {str(e)}')

        return redirect('trabajadores_list')

    # GET request - mostrar confirmación de eliminación
    context = {
        'trabajador': trabajador,
    }
    return render(request, 'trabajadores_confirm_delete.html', context)
