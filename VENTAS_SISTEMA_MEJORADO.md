# 📋 SISTEMA DE GESTIÓN DE VENTAS MEJORADO - DOCUMENTACIÓN TÉCNICA

## 🎯 Descripción General

Se ha implementado un sistema mejorado de gestión de ventas que permite:
- ✅ Crear ventas con múltiples productos
- ✅ Editar ventas después de finalizarlas (agregar productos, aumentar cantidades)
- ✅ Registrar pagos parciales en ventas a crédito (abonos)
- ✅ Recálculo automático de totales y ganancias
- ✅ Historial de auditoría preservado en DetalleVenta

---

## 🏗️ ARQUITECTURA IMPLEMENTADA

### 1. MODELOS (models.py)

Mantiene los modelos existentes sin cambios:
- **Venta**: Registro principal de transacción
- **DetalleVenta**: Desglose de productos por venta (audit trail)
- **Cobro**: Registro de pagos/abonos en ventas a crédito

### 2. FORMULARIOS (forms.py) - NUEVO

```python
VentaForm()           # Crear/editar venta (cliente, tipo_pago, método_pago)
DetalleVentaForm()    # Agregar productos (producto, cantidad, precio_venta)
EditarVentaForm()     # Editar venta existente (agregar/aumentar productos)
CobroForm()           # Registrar pagos/abonos
```

### 3. VISTAS (views.py) - EXTENDIDAS

#### Vistas Principales:

| Vista | Ruta | Descripción |
|-------|------|-------------|
| `ventas_form()` | `/ventas/` | Crear nueva venta (EXISTENTE) |
| `lista_ventas()` | `/ventas/lista/` | Listar todas las ventas con filtros |
| `detalle_venta()` | `/ventas/<id>/detalle/` | Ver detalles de una venta |
| `editar_venta()` | `/ventas/<id>/editar/` | Editar/agregar productos a venta |
| `agregar_pago()` | `/ventas/<id>/pago/` | Registrar pago a crédito |
| `eliminar_detalle()` | `/ventas/<id>/detalle/<id>/eliminar/` | Eliminar producto de venta |

#### Función Auxiliar Crítica:

```python
recalcular_totales_venta(venta)
```

**Función nuclear** que recalcula automáticamente:
- Cantidad total de la venta
- Total en dinero (sum de subtotales)
- Ganancia total (sum de ganancias)
- Precios promedio (si múltiples productos)

**Invocada en:**
- Agregar producto nuevo
- Aumentar cantidad de producto existente
- Eliminar producto
- Modificar precio

### 4. TEMPLATES - NUEVOS

```
ventas_lista.html       → Lista de ventas con filtros
venta_detalle.html      → Detalle completo de venta
venta_editar.html       → Formulario para editar venta
venta_pago.html         → Formulario para registrar pagos
```

### 5. RUTAS (urls.py) - ACTUALIZADAS

```python
path('', views.ventas_form, name='ventas')  # EXISTENTE
path('lista/', views.lista_ventas, name='lista_ventas')  # NUEVO
path('<int:venta_id>/detalle/', views.detalle_venta, name='detalle_venta')  # NUEVO
path('<int:venta_id>/editar/', views.editar_venta, name='editar_venta')  # NUEVO
path('<int:venta_id>/pago/', views.agregar_pago, name='agregar_pago')  # NUEVO
path('<int:venta_id>/detalle/<int:detalle_id>/eliminar/', views.eliminar_detalle, name='eliminar_detalle')  # NUEVO
```

---

## 💡 FLUJO DE TRABAJO

### Scenario 1: Crear y Finalizar Venta

```
1. Usuario va a /ventas/
2. Completa formulario con:
   - Cliente: "Valentina Clavijo"
   - Producto 1: 30 kg Papa Primera @ $250/kg = $7,500
   - Producto 2: 20 kg Rechazo Medio @ $70/kg = $1,400
   - Tipo de pago: "Pago Completo"
3. Sistema crea:
   - 1 registro Venta (total=$8,900, ganancia=...)
   - 2 registros DetalleVenta (uno por producto)
4. Venta se registra como PAGADA
```

### Scenario 2: Editar Venta Después (Agregar Producto)

```
1. Usuario ve venta en /ventas/lista/
2. Hace clic en "Editar Venta"
3. Elige acción: "Agregar nuevo producto"
4. Selecciona: 15 kg Tronco @ $80/kg
5. Sistema:
   - Valida que NO esté ya en la venta
   - Crea nuevo DetalleVenta
   - Llama recalcular_totales_venta()
   - Venta ahora: total=$9,700, cantidad=65kg, ganancia=...
   - Preserva todos los DetalleVenta anteriores (audit trail)
```

### Scenario 3: Editar Venta (Aumentar Cantidad)

```
1. Usuario selecciona: "Aumentar cantidad de existente"
2. Elige: Papa Primera + 10 kg
3. Sistema:
   - Busca DetalleVenta existente
   - Actualiza: cantidad: 30→40 kg
   - Recalcula subtotal y ganancia del detalle
   - Recalcula totales de la venta
   - DetalleVenta original se mantiene pero actualizado
```

### Scenario 4: Venta a Crédito con Abonos

```
1. Crear venta "Pago a Crédito":
   - Total: $8,900
   - Inicial pagado: $3,000
   - Saldo pendiente: $5,900
   - Vencimiento: 15 días

2. Días después, usuario va a /ventas/<id>/detalle/
3. Hace clic "Registrar Pago"
4. Ingresa abono: $2,000
5. Sistema:
   - Crea registro Cobro ($2,000)
   - Actualiza venta: monto_pagado = $5,000
   - Saldo pendiente ahora: $3,900
   - Estado = "pendiente" (aún debe)

6. Nuevo abono de $3,900:
   - Estado = "pagado" ✓
   - Sistema reconoce: pagado >= total
```

---

## ✅ CARACTERÍSTICAS CLAVE IMPLEMENTADAS

### 1. Recálculo Automático
- **ORM-only**: Usa `Sum()` y agregación de Django, NO raw SQL
- **Atómico**: Usa `transaction.atomic()` para consistencia
- **Triggers**: Recalculation se ejecuta automáticamente en:
  - `editar_venta()` después de cambios
  - `agregar_pago()` después de cobro
  - `eliminar_detalle()` después de eliminar

### 2. Validaciones Robustas

#### En Forms:
```python
# CobroForm valida:
- Monto > 0
- Monto <= saldo_pendiente

# EditarVentaForm valida:
- Producto existe
- Cantidad > 0
- Si "aumentar cantidad": producto ya está en venta

# DetalleVentaForm valida:
- Cantidad > 0
- Precio > 0
```

#### En Views:
```python
# editar_venta():
- Solo para ventas sin pagar completamente
- Valida que producto no esté duplicado
- Lanza excepción si DetalleVenta no existe

# agregar_pago():
- Solo para ventas tipo 'fiado'
- Solo si saldo_pendiente > 0
- Validación de monto_pagado vs total
```

### 3. Seguridad

- `@login_required` en todas las nuevas vistas
- `transaction.atomic()` previene estados inconsistentes
- Validación de permisos (usuario solo ve sus datos)
- CSRF protection en todos los formularios

### 4. Historial/Auditoría

- Todos los DetalleVenta se preservan (nunca se eliminan completamente)
- Cada cambio crea nuevo registro si es agregar
- Timestamps automáticos en Cobro (fecha auto_now_add)
- Búsqueda de cambios en venta: revisar todos DetalleVenta

### 5. Interfaz Amigable

- Filtros por estado (pagado/pendiente/vencido)
- Filtros por cliente
- Filtros por período (hoy/semana/mes)
- Resumen de estadísticas
- Badges visuales de estado
- Iconos Font Awesome

---

## 🔧 INSTALACIÓN Y CONFIGURACIÓN

### 1. Verificar Archivos Creados

```bash
# Forms
ls -la apps/ventas/forms.py

# Templates
ls -la apps/ventas/templates/ventas_*.html
ls -la apps/ventas/templates/venta_*.html

# URLs actualizadas
cat apps/ventas/urls.py

# Views actualizadas
head -20 apps/ventas/views.py
```

### 2. Validar Proyecto

```bash
python manage.py check
```

### 3. Crear Migraciones (si hay cambios en modelos)

```bash
python manage.py makemigrations ventas
python manage.py migrate
```

### 4. Cargar Datos

```bash
python manage.py loaddata registros.json
```

### 5. Crear Superusuario (si no existe)

```bash
python manage.py createsuperuser
```

### 6. Ejecutar Servidor

```bash
python manage.py runserver
```

---

## 🧪 CASOS DE PRUEBA

### Test 1: Crear Venta Simple

```bash
# Acceder a http://localhost:8000/ventas/
# Cliente: Valentina Clavijo
# Producto 1: Papa Primera, 30 kg
# Tipo: Pago Completo
# Enviar formulario
# ✓ Debe crear venta con total $7,500
```

### Test 2: Editar Venta (Agregar Producto)

```bash
# Desde venta creada, click "Editar Venta"
# Acción: Agregar nuevo producto
# Producto: Rechazo Medio, 20 kg, $70/kg
# ✓ Total debe ser $8,900
# ✓ Debe haber 2 DetalleVenta
```

### Test 3: Editar Venta (Aumentar Cantidad)

```bash
# Acción: Aumentar cantidad
# Producto: Papa Primera, +10 kg
# ✓ Total debe ser $9,750
# ✓ DetalleVenta debe mostrar 40 kg
```

### Test 4: Venta a Crédito

```bash
# Crear venta tipo "Pago a Crédito"
# Total: $8,900, Pagado inicial: $2,000
# ✓ Estado debe ser "pendiente"
# ✓ Saldo pendiente: $6,900
```

### Test 5: Registrar Pagos

```bash
# Desde detalle de venta a crédito
# Click "Registrar Pago"
# Abono 1: $3,000 → Saldo: $3,900
# Abono 2: $3,900 → Saldo: $0, Estado: pagado
# ✓ Debe haber 2 registros Cobro
```

### Test 6: Listar Ventas con Filtros

```bash
# Ir a /ventas/lista/
# Filtro estado: "pendiente"
# Filtro período: "mes"
# ✓ Debe mostrar solo ventas pendientes del mes actual
# ✓ Estadísticas deben sumar correctamente
```

---

## 📊 EJEMPLOS CON DATOS REALES (registros.json)

### Productos Disponibles:
- Papa Primera: $70,000/kg (proveedor: RH)
- Tronco: $70,000/kg (proveedor: RH)
- Rechazo Medio: $70,000/kg (proveedor: RH)
- Rechazo Grueso: $62,500/kg (proveedor: RH)
- Sobrante: $62,500/kg (proveedor: RH)
- Medio Pollo: $100,000/kg (proveedor: CityPapa)
- Tercera: $100,000/kg (proveedor: CityPapa)

### Clientes Disponibles:
- Samuel Piñeres
- Juan Sebastián Clavijo
- Valentina Clavijo
- Mateo Arrubla
- Consumidor Final

### Ejemplo de Creación:

```
Cliente: Valentina Clavijo
Producto 1: Papa Primera, 30 kg @ $70,000/kg = $2,100,000
Producto 2: Rechazo Medio, 20 kg @ $70,000/kg = $1,400,000
---
Total: $3,500,000
Ganancia: Depende del precio de compra
Tipo: Pago a Crédito
Plazo: 15 días
Pagado inicial: $1,000,000
Saldo: $2,500,000
```

---

## 🚨 MANEJO DE ERRORES

### Error: "El producto no está en esta venta"
**Causa**: Intentó "aumentar cantidad" de un producto que no existe en la venta
**Solución**: Use "Agregar nuevo producto" en su lugar

### Error: "El monto no puede exceder el saldo pendiente"
**Causa**: Ingresó abono mayor al saldo
**Solución**: Ingrese cantidad <= saldo_pendiente

### Error: "Stock insuficiente"
**Causa**: Cantidad solicitada > stock disponible (NOTA: De la vista original)
**Solución**: Reduzca la cantidad

### Error: "Validación de formulario fallida"
**Causa**: Campo requerido vacío o valor inválido
**Solución**: Revise que todos los campos estén completados

---

## 🔍 DEBUGGING

### Ver estado de una venta:
```bash
python manage.py shell
from apps.ventas.models import Venta, DetalleVenta, Cobro

venta = Venta.objects.get(idVenta=30)
print(f"Total: ${venta.total}")
print(f"Pagado: ${venta.monto_pagado}")
print(f"Saldo: ${venta.saldo_pendiente}")

# Ver detalles
for detalle in venta.detalles.all():
    print(f"- {detalle.producto}: {detalle.cantidad}kg @ ${detalle.precio_venta}")

# Ver cobros
for cobro in venta.cobros.all():
    print(f"- Pago ${cobro.monto} el {cobro.fecha}")
```

### Recalcular venta manualmente:
```bash
from apps.ventas.views import recalcular_totales_venta

venta = Venta.objects.get(idVenta=30)
recalcular_totales_venta(venta)
print(f"Nuevo total: ${venta.total}")
```

---

## 📝 NOTAS IMPORTANTES

1. **Stock NO se deduce**: El sistema registra ventas pero NO modifica `productos.stock`. 
   Esto es intencional (sistema de tracking, no de inventario real).

2. **Transacciones Atómicas**: Todos los cambios se hacen dentro de `transaction.atomic()` 
   para garantizar que la BD nunca queda en estado inconsistente.

3. **ORM Only**: No se usa raw SQL. Todas las operaciones usan Django ORM 
   (`Sum()`, `Count()`, `aggregate()`, etc.).

4. **Recálculo Garantizado**: Cada vez que se modifica una venta, `recalcular_totales_venta()` 
   se ejecuta automáticamente.

5. **Preservación de Datos**: Los DetalleVenta nunca se eliminan completamente, 
   proporcionando un historial completo de auditoría.

---

## 🎓 PRÓXIMAS MEJORAS (Opcionales)

- [ ] API REST para integración con aplicaciones móviles
- [ ] Reportes en PDF con desglose de ventas
- [ ] Notificaciones de vencimientos próximos
- [ ] Integración con pasarela de pagos
- [ ] Descuentos y promociones
- [ ] Sistema de comisiones
- [ ] Análisis de tendencias

---

**Documento generado**: 1 de mayo de 2026
**Versión**: 1.0 - Producción Ready
