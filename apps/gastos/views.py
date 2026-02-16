from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import Gastos
from apps.proveedores.models import Proveedores


def gastos_list(request):
    """Vista principal de gastos con listado y formulario."""
    gastos = Gastos.objects.all()
    proveedores = Proveedores.objects.all()
    
    # Calcular totales
    hoy = timezone.now().date()
    
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
    gastos_hoy = gastos.filter(fecha__date=hoy).aggregate(total=Sum('monto'))['total'] or 0
    cantidad_gastos = gastos.count()
    
    # Gastos por categoría
    gastos_por_categoria = {}
    for categoria, nombre in Gastos.CATEGORIA_CHOICES:
        total = gastos.filter(categoria=categoria).aggregate(total=Sum('monto'))['total'] or 0
        gastos_por_categoria[categoria] = {
            'nombre': nombre,
            'total': total
        }
    
    context = {
        'gastos': gastos,
        'proveedores': proveedores,
        'total_gastos': total_gastos,
        'gastos_hoy': gastos_hoy,
        'cantidad_gastos': cantidad_gastos,
        'gastos_por_categoria': gastos_por_categoria,
        'categorias': Gastos.CATEGORIA_CHOICES,
    }
    return render(request, 'gastos.html', context)


def gastos_crear(request):
    """Crear un nuevo gasto."""
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        monto = request.POST.get('monto', '0')
        categoria = request.POST.get('categoria', 'otros')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora', '00:00')
        proveedor_id = request.POST.get('proveedor')
        
        # Validaciones
        if not descripcion:
            messages.error(request, 'La descripción es obligatoria.')
            return redirect('gastos')
        
        try:
            monto = Decimal(monto)
            if monto <= 0:
                messages.error(request, 'El monto debe ser mayor a 0.')
                return redirect('gastos')
        except (InvalidOperation, ValueError):
            messages.error(request, 'El monto debe ser un número válido.')
            return redirect('gastos')
        
        # Combinar fecha y hora
        try:
            if fecha and hora:
                fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
                fecha_hora = timezone.make_aware(fecha_hora)
            elif fecha:
                fecha_hora = datetime.strptime(fecha, "%Y-%m-%d")
                fecha_hora = timezone.make_aware(fecha_hora)
            else:
                fecha_hora = timezone.now()
        except ValueError:
            fecha_hora = timezone.now()
        
        # Obtener proveedor si existe
        proveedor = None
        if proveedor_id:
            try:
                proveedor = Proveedores.objects.get(idProveedor=proveedor_id)
            except Proveedores.DoesNotExist:
                pass
        
        # Crear el gasto
        Gastos.objects.create(
            descripcion=descripcion,
            monto=monto,
            categoria=categoria,
            fecha=fecha_hora,
            proveedor=proveedor
        )
        
        messages.success(request, f'Gasto "{descripcion}" registrado exitosamente.')
        return redirect('gastos')
    
    return redirect('gastos')


def gastos_editar(request, pk):
    """Editar un gasto existente."""
    gasto = get_object_or_404(Gastos, idGasto=pk)
    
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        monto = request.POST.get('monto', '0')
        categoria = request.POST.get('categoria', 'otros')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora', '00:00')
        proveedor_id = request.POST.get('proveedor')
        
        # Validaciones
        if not descripcion:
            messages.error(request, 'La descripción es obligatoria.')
            return redirect('gastos')
        
        try:
            monto = Decimal(monto)
            if monto <= 0:
                messages.error(request, 'El monto debe ser mayor a 0.')
                return redirect('gastos')
        except (InvalidOperation, ValueError):
            messages.error(request, 'El monto debe ser un número válido.')
            return redirect('gastos')
        
        # Combinar fecha y hora
        try:
            if fecha and hora:
                fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
                fecha_hora = timezone.make_aware(fecha_hora)
            elif fecha:
                fecha_hora = datetime.strptime(fecha, "%Y-%m-%d")
                fecha_hora = timezone.make_aware(fecha_hora)
            else:
                fecha_hora = gasto.fecha
        except ValueError:
            fecha_hora = gasto.fecha
        
        # Obtener proveedor si existe
        proveedor = None
        if proveedor_id:
            try:
                proveedor = Proveedores.objects.get(idProveedor=proveedor_id)
            except Proveedores.DoesNotExist:
                pass
        
        # Actualizar el gasto
        gasto.descripcion = descripcion
        gasto.monto = monto
        gasto.categoria = categoria
        gasto.fecha = fecha_hora
        gasto.proveedor = proveedor
        gasto.save()
        
        messages.success(request, f'Gasto "{descripcion}" actualizado exitosamente.')
        return redirect('gastos')
    
    return redirect('gastos')


def gastos_eliminar(request, pk):
    """Eliminar un gasto."""
    gasto = get_object_or_404(Gastos, idGasto=pk)
    
    if request.method == 'POST':
        descripcion = gasto.descripcion
        gasto.delete()
        messages.success(request, f'Gasto "{descripcion}" eliminado exitosamente.')
    
    return redirect('gastos')
