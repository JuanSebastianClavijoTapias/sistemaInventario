# 🚀 QUICK START - GUÍA RÁPIDA DE USO

## Acceso a las Nuevas Funcionalidades

### URLs Principales

```
Crear Venta:           http://localhost:8000/ventas/
Listar Ventas:         http://localhost:8000/ventas/lista/
Ver Detalle:           http://localhost:8000/ventas/30/detalle/
Editar Venta:          http://localhost:8000/ventas/30/editar/
Registrar Pago:        http://localhost:8000/ventas/30/pago/
```

---

## ✨ Ejemplo Práctico Completo

### Paso 1: Crear Venta Inicial

```
Navegue a: http://localhost:8000/ventas/

Formulario:
- Cliente: "Valentina Clavijo"
- Producto 1:
  * Seleccionar: "Papa Primera"
  * Cantidad: 30 kg
  * Precio: 250,000 $/kg
  
- Producto 2:
  * Seleccionar: "Rechazo Medio"
  * Cantidad: 20 kg
  * Precio: 70,000 $/kg

- Tipo de Pago: "Pago a Crédito"
- Método: "Efectivo"
- Días de Crédito: 15
- Monto Inicial: 1,000,000

Resultado esperado:
✓ Total: $8,900,000
✓ Pagado: $1,000,000
✓ Pendiente: $7,900,000
✓ ID Venta: 33 (o el siguiente)
```

### Paso 2: Editar Venta (Agregar Producto)

```
Navegue a: http://localhost:8000/ventas/33/editar/

Información Actual:
- Total: $8,900,000
- Cantidad: 50 kg
- Ganancia: Calculada

Acciones:
1. Seleccionar radio: "Agregar nuevo producto"
2. Producto: "Tronco"
3. Cantidad: 15 kg
4. Precio: 80,000 $/kg
5. Click "Aplicar Cambios"

Resultado esperado:
✓ Total actualizado: $9,100,000
✓ Cantidad: 65 kg
✓ 3 DetalleVenta en la BD
✓ Mensaje de éxito
```

### Paso 3: Editar Venta (Aumentar Cantidad)

```
Navegue a: http://localhost:8000/ventas/33/editar/

1. Seleccionar radio: "Aumentar cantidad de existente"
2. Producto: "Papa Primera"
3. Cantidad: 10 kg (se SUMA a los 30 existentes)
4. Precio: 250,000 $/kg
5. Click "Aplicar Cambios"

Resultado esperado:
✓ Total actualizado: $9,350,000
✓ Papa Primera ahora: 40 kg (30 + 10)
✓ DetalleVenta actualizado en lugar de crear nuevo
```

### Paso 4: Registrar Pagos

```
Navegue a: http://localhost:8000/ventas/33/detalle/
Click botón: "Registrar Pago"

Pantalla muestra:
- Cliente: Valentina Clavijo
- Total: $9,350,000
- Pagado: $1,000,000
- Saldo: $8,350,000

Ingrese abono: 3,000,000
Click "Registrar Pago"

Resultado esperado:
✓ Mensaje: "Abono registrado por $3,000,000"
✓ Nuevo saldo: $5,350,000
✓ Estado: "pendiente"

Nuevo abono: 5,350,000
Click "Registrar Pago"

Resultado esperado:
✓ Mensaje: "¡Venta completamente pagada!"
✓ Nuevo saldo: $0
✓ Estado: "pagado" ✓
✓ 2 registros de Cobro en la BD
```

---

## 📊 Vista de Lista de Ventas

```
URL: http://localhost:8000/ventas/lista/

Filtros disponibles:
- Estado: Todos / Pagado / Pendiente / Vencido
- Cliente: Todos / [Nombre cliente]
- Período: Todo / Hoy / Últimos 7 días / Este mes

Estadísticas mostradas:
- Total de Ventas: $XX,XXX,XXX
- Total Pagado: $X,XXX,XXX
- Por Cobrar: $XX,XXX,XXX
- Cantidad de Ventas: NN

Tabla de ventas con:
- ID
- Cliente
- Productos
- Total
- Pagado
- Estado (badge color)
- Fecha
- Acciones (Ver / Editar)
```

---

## 💻 Comandos Django Shell

### Ver todas las ventas de un cliente

```python
from apps.ventas.models import Venta
from apps.clientes.models import Clientes

cliente = Clientes.objects.get(nombre="Valentina")
ventas = Venta.objects.filter(cliente=cliente).order_by('-fecha')

for venta in ventas:
    print(f"Venta #{venta.idVenta}: ${venta.total} - {venta.estado_pago}")
```

### Ver detalles de una venta específica

```python
venta = Venta.objects.get(idVenta=33)

print(f"Venta #{venta.idVenta}")
print(f"Cliente: {venta.cliente.nombre}")
print(f"Total: ${venta.total}")
print(f"Pagado: ${venta.monto_pagado}")
print(f"Saldo: ${venta.saldo_pendiente}")
print(f"Estado: {venta.estado_pago}")
print()
print("Productos:")

for detalle in venta.detalles.all():
    print(f"  - {detalle.producto.nombre}: {detalle.cantidad}kg @ ${detalle.precio_venta}")

print()
print("Pagos realizados:")
for cobro in venta.cobros.all():
    print(f"  - ${cobro.monto} el {cobro.fecha.strftime('%d/%m/%Y %H:%M')}")
```

### Listar ventas pendientes

```python
from django.utils import timezone

ventas_pendientes = Venta.objects.filter(
    estado_pago='pendiente'
).select_related('cliente').order_by('fecha_vencimiento')

for venta in ventas_pendientes:
    dias = venta.dias_para_vencimiento
    print(f"Venta #{venta.idVenta}: {venta.cliente.nombre} - Debe: ${venta.saldo_pendiente} (vence en {dias} días)")
```

### Calcular total de ventas del mes

```python
from django.db.models import Sum
from django.utils import timezone

hoy = timezone.localdate()
inicio_mes = hoy.replace(day=1)

total_mes = Venta.objects.filter(
    fecha__date__gte=inicio_mes
).aggregate(total=Sum('total'))['total'] or 0

print(f"Total ventas del mes: ${total_mes}")
```

---

## 🎨 Características Visuales

### Badges de Estado

- 🟢 **Pagado** (verde): Venta completamente pagada
- 🟡 **Pendiente** (naranja): Venta a crédito con saldo
- 🔴 **Vencido** (rojo): Plazo de crédito venció

### Iconos Utilizados

- 📝 Historia
- ✅ Checkmark
- ✏️ Editar
- 👁️ Ver
- ➕ Agregar
- 💰 Pagos
- 📊 Estadísticas
- 🔍 Buscar

---

## ⚠️ Casos de Uso Especiales

### Caso 1: Venta que debe modificarse urgente

```
Escenario: Se cometió error, necesita aumentar cantidad

1. Ir a /ventas/33/editar/
2. Seleccionar "Aumentar cantidad"
3. Seleccionar producto correcto
4. Agregar cantidad faltante
5. El sistema recalcula automáticamente
6. El cliente ve el nuevo total al momento
```

### Caso 2: Cliente paga parcialmente

```
Escenario: Venta $10,000,000 - Cliente paga $3,000,000

1. Crear venta a crédito por $10,000,000
2. Ir a detalle y click "Registrar Pago"
3. Ingresa $3,000,000
4. Sistema:
   - Saldo: $7,000,000
   - Estado: "pendiente"
5. Semana después: otro abono de $4,000,000
6. Saldo: $3,000,000
7. Último abono de $3,000,000 → Pagado ✓
```

### Caso 3: Vencimiento de crédito

```
Escenario: Venta vence en 15 días pero no se paga

1. Sistema detecta fecha_vencimiento < hoy
2. Vista /ventas/lista/ muestra estado "vencido"
3. Alerta roja en historial
4. Usuario puede seguir agregando pagos parciales
5. Una vez pagado → Estado "pagado"
```

---

## 🔐 Permisos y Seguridad

### Quién puede acceder

- ✅ Usuarios autenticados (`@login_required`)
- ✅ Superusarios
- ✅ Personal autorizado

### Quién NO puede

- ❌ Usuarios no autenticados → Redirige a login
- ❌ Ver ventas de otros usuarios (depende de implementación)

### Protecciones implementadas

- ✅ CSRF token en todos los formularios
- ✅ Validación de datos en el servidor
- ✅ Transacciones atómicas
- ✅ No hay inyección SQL (ORM only)

---

## 📞 Soporte Técnico

### Error: "Formulario inválido"

```
Verificar:
1. Todos los campos requeridos completados
2. Números válidos (sin símbolos)
3. Producto existe en la BD
4. Cliente existe en la BD
```

### Error: "Producto ya está en esta venta"

```
Solución:
- Use "Aumentar cantidad de existente" en lugar de "Agregar nuevo"
```

### Error: "Monto excede saldo pendiente"

```
Solución:
- Ingrese cantidad menor o igual al saldo
- Monto máximo: $SALDO_PENDIENTE
```

### Error: "DetalleVenta no encontrado"

```
Significa:
- Intentó aumentar cantidad de producto que no está
- Solución: Use "Agregar nuevo producto"
```

---

## 📈 Métricas y Reportes

### Información disponible en lista de ventas

1. **Total de Ventas**: Suma de todos los totales de venta
2. **Total Pagado**: Suma de montos_pagados
3. **Por Cobrar**: Total - Pagado (saldo pendiente total)
4. **Cantidad de Ventas**: Número de registros Venta

### En detalle de venta

1. Productos y cantidades exactas
2. Precios unitarios
3. Subtotales y ganancias
4. Historial completo de pagos
5. Fecha de vencimiento y días restantes

---

**Última actualización**: 1 de mayo de 2026
