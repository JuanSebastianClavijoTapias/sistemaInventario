# 🏗️ ARQUITECTURA DEL SISTEMA DE VENTAS MEJORADO

## 📐 FLUJO DE DATOS

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USUARIO (Browser)                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                ┌──────────────┴───────────────┐
                │                              │
        ┌───────▼────────┐          ┌─────────▼─────────┐
        │  Crear Venta   │          │  Ver Historial    │
        │   (/ventas/)   │          │ (/ventas/lista/)  │
        └────────┬───────┘          └─────────┬─────────┘
                 │                            │
        ┌────────▼──────────┐        ┌────────▼─────────┐
        │  VentaForm        │        │  Filtros         │
        │  - Cliente        │        │  - Estado        │
        │  - Tipo Pago      │        │  - Cliente       │
        │  - Método Pago    │        │  - Período       │
        └────────┬──────────┘        └────────┬─────────┘
                 │                            │
        ┌────────▼──────────────────────────┬┘
        │                                   │
        │      ┌──────────────────────────────────┐
        │      │  BASE DE DATOS                   │
        │      │                                  │
        └─────►│  Venta (Master Record)           │
               │  - idVenta                       │
               │  - cliente_id (FK)               │
               │  - total                         │
               │  - tipo_pago                     │
               │  - estado_pago                   │
               │  - monto_pagado                  │
               │  - fecha_vencimiento             │
               │                                  │
               │  DetalleVenta (Audit Trail)     │
               │  - venta_id (FK)                 │
               │  - producto_id (FK)              │
               │  - cantidad                      │
               │  - precio_venta                  │
               │  - subtotal                      │
               │  - ganancia                      │
               │                                  │
               │  Cobro (Payment History)        │
               │  - venta_id (FK)                 │
               │  - monto                         │
               │  - fecha                         │
               │                                  │
               │  Clientes (Linked)               │
               │  Productos (Linked)              │
               └──────────────────────────────────┘
```

---

## 🔄 CICLO DE VIDA DE UNA VENTA

### Estado 1: CREAR

```
Entrada:
┌─────────────────────────────────┐
│ Cliente: Valentina              │
│ Producto 1: Papa Primera 30kg    │
│ Producto 2: Rechazo 20kg         │
│ Tipo: Crédito                    │
│ Pagado Inicial: $1,000,000       │
└─────────────────────────────────┘
         │
         ├─► VentaForm.is_valid()
         │
         ├─► Crear Venta(
         │      total=$8,900,000,
         │      monto_pagado=$1,000,000,
         │      estado_pago='pendiente'
         │   )
         │
         └─► Crear DetalleVenta x2
                 ├─ Papa Primera 30kg
                 └─ Rechazo 20kg

Output:
┌─────────────────────────────────┐
│ ✅ Venta #33 Creada             │
│ Total: $8,900,000               │
│ Estado: Pendiente               │
│ Saldo: $7,900,000               │
└─────────────────────────────────┘
```

### Estado 2: EDITAR (Agregar Producto)

```
Input:
┌─────────────────────────────────┐
│ Acción: Agregar nuevo           │
│ Producto: Tronco                │
│ Cantidad: 15kg                  │
│ Precio: $80,000/kg              │
└─────────────────────────────────┘
         │
         ├─► EditarVentaForm.is_valid()
         │
         ├─► Verificar que no existe
         │   Tronco en esta venta
         │
         ├─► Crear DetalleVenta #3
         │   (Tronco 15kg)
         │
         └─► recalcular_totales_venta()
                 │
                 ├─ Sum(cantidad) = 65kg
                 ├─ Sum(subtotal) = $9,100,000
                 └─ Sum(ganancia) = $X,XXX,XXX

Output:
┌─────────────────────────────────┐
│ ✅ Producto Agregado             │
│ Nuevo Total: $9,100,000         │
│ Cantidad: 65kg                  │
│ DetalleVenta: 3 registros       │
└─────────────────────────────────┘
```

### Estado 3: EDITAR (Aumentar Cantidad)

```
Input:
┌─────────────────────────────────┐
│ Acción: Aumentar cantidad       │
│ Producto: Papa Primera          │
│ Cantidad Adicional: 10kg        │
│ Precio: $250,000/kg             │
└─────────────────────────────────┘
         │
         ├─► Obtener DetalleVenta
         │   donde producto=Papa Primera
         │
         ├─► Actualizar DetalleVenta
         │   cantidad: 30 → 40kg
         │   subtotal: 7,500,000 → 10,000,000
         │
         └─► recalcular_totales_venta()
                 │
                 ├─ Sum(cantidad) = 75kg
                 ├─ Sum(subtotal) = $9,750,000
                 └─ Update Venta

Output:
┌─────────────────────────────────┐
│ ✅ Cantidad Aumentada            │
│ Nuevo Total: $9,750,000         │
│ Papa Primera: 30 → 40kg         │
│ DetalleVenta: 3 (actualizado)   │
└─────────────────────────────────┘
```

### Estado 4: PAGAR (Abono 1)

```
Input:
┌─────────────────────────────────┐
│ Monto Abono: $2,000,000         │
│ Saldo Pendiente: $7,900,000     │
└─────────────────────────────────┘
         │
         ├─► CobroForm.is_valid()
         │   Valida: monto ≤ saldo
         │
         ├─► Crear Cobro(
         │      venta_id=33,
         │      monto=$2,000,000
         │   )
         │
         ├─► Actualizar Venta
         │   monto_pagado += $2,000,000
         │
         └─► actualizar_estado_pago()
                 Si monto_pagado < total
                 → estado_pago = 'pendiente'

Output:
┌─────────────────────────────────┐
│ ✅ Abono Registrado             │
│ Pagado: $1,000,000 → $3,000,000 │
│ Saldo: $7,900,000 → $5,900,000  │
│ Estado: Pendiente               │
│ Cobro #1 registrado             │
└─────────────────────────────────┘
```

### Estado 5: PAGAR (Abono 2 - Final)

```
Input:
┌─────────────────────────────────┐
│ Monto Abono: $5,900,000         │
│ Saldo Pendiente: $5,900,000     │
└─────────────────────────────────┘
         │
         ├─► CobroForm.is_valid()
         │
         ├─► Crear Cobro(
         │      venta_id=33,
         │      monto=$5,900,000
         │   )
         │
         ├─► Actualizar Venta
         │   monto_pagado = $9,750,000
         │
         └─► actualizar_estado_pago()
                 Si monto_pagado >= total
                 → estado_pago = 'pagado' ✓

Output:
┌─────────────────────────────────┐
│ ✅ VENTA COMPLETAMENTE PAGADA   │
│ Pagado: $9,750,000              │
│ Saldo: $0                       │
│ Estado: PAGADO ✓                │
│ Cobro #2 registrado             │
└─────────────────────────────────┘
```

---

## 🎯 MATRIZ DE FUNCIONES Y RESPONSABILIDADES

```
┌──────────────────┬──────────────┬────────────────┬─────────────────┐
│ Función          │ Parámetros   │ Responsabilidad│ Output          │
├──────────────────┼──────────────┼────────────────┼─────────────────┤
│ ventas_form()    │ request      │ Crear venta    │ Venta + Detalles│
├──────────────────┼──────────────┼────────────────┼─────────────────┤
│ lista_ventas()   │ request      │ Listar + filtro│ HTML + contexto │
├──────────────────┼──────────────┼────────────────┼─────────────────┤
│ detalle_venta()  │ request, id  │ Mostrar detalles│ HTML completo  │
├──────────────────┼──────────────┼────────────────┼─────────────────┤
│ editar_venta()   │ request, id  │ Agregar/aumentar│ Venta actualiz.│
├──────────────────┼──────────────┼────────────────┼─────────────────┤
│ agregar_pago()   │ request, id  │ Registrar cobro│ Cobro + Venta   │
├──────────────────┼──────────────┼────────────────┼─────────────────┤
│ recalcular_*()   │ venta        │ Recalc. totales│ Venta guardada  │
└──────────────────┴──────────────┴────────────────┴─────────────────┘
```

---

## 🔐 VALIDACIONES EN CASCADA

```
INPUT (Usuario)
    │
    ▼
┌────────────────────────────────┐
│ Frontend Validation (Optional) │ ← type="number", required
└────────────────────────────────┘
    │
    ▼
┌────────────────────────────────┐
│ Form Validation (forms.py)     │ ← clean_* methods
│ - Cantidad > 0                 │
│ - Precio > 0                   │
│ - Monto ≤ saldo                │
│ - Producto existe              │
└────────────────────────────────┘
    │ ✅ Válido
    ▼
┌────────────────────────────────┐
│ View Validation (views.py)     │ ← lógica de negocio
│ - Venta existe                 │
│ - Producto no duplicado        │
│ - Estado correcto              │
│ - Usuario autenticado          │
└────────────────────────────────┘
    │ ✅ Válido
    ▼
┌────────────────────────────────┐
│ Database Transaction.atomic()  │ ← all-or-nothing
│ - Crear registros              │
│ - Actualizar cálculos          │
│ - Si error → rollback          │
└────────────────────────────────┘
    │ ✅ Éxito
    ▼
OUTPUT (BD + Respuesta Usuario)
```

---

## 📊 DIAGRAMA DE RELACIONES

```
┌─────────────────────────────────────────────────┐
│               Clientes                          │
│  ┌────────────────────────────────┐             │
│  │ idCliente (PK)                 │             │
│  │ nombre                         │             │
│  │ apellido                       │             │
│  │ teléfono                       │             │
│  │ inicial                        │             │
│  │ saldo                          │             │
│  └────────────────────────────────┘             │
└────────────┬────────────────────────────────────┘
             │
             │ 1:N (has many)
             │
    ┌────────▼─────────────────────────────────────┐
    │            Venta                             │
    │  ┌─────────────────────────────────────────┐ │
    │  │ idVenta (PK)                            │ │
    │  │ cliente_id (FK) ◄────────────────┐      │ │
    │  │ producto_id (FK, nullable)       │      │ │
    │  │ cantidad                         │      │ │
    │  │ total                            │      │ │
    │  │ precio_compra, precio_venta      │      │ │
    │  │ ganancia                         │      │ │
    │  │ tipo_pago (completo/fiado)      │      │ │
    │  │ monto_pagado                     │      │ │
    │  │ estado_pago                      │      │ │
    │  │ fecha_vencimiento                │      │ │
    │  │ metodo_pago                      │      │ │
    │  │ fecha                            │      │ │
    │  └─────────────────────────────────────────┘ │
    └────┬──────────┬──────────┬────────────────────┘
         │          │          │
         │ 1:N      │ 1:N      │ 1:N
         │          │          │
    ┌────▼────┐┌────▼───────┐┌───▼──────────────┐
    │Detalle  ││ Cobro      ││  Productos       │
    │Venta    ││(Payments)  ││                  │
    │         ││            ││  ┌─────────────┐ │
    │venta_id ││venta_id   ││ │idProducto   │ │
    │producto ││monto      ││ │nombre        │ │
    │cantidad ││fecha      ││ │categoria     │ │
    │precio_  ││           ││ │precio_compra │ │
    │venta    ││           ││ │precio_venta  │ │
    │subtotal ││           ││ │stock         │ │
    │ganancia ││           ││ │proveedor_id  │ │
    │         ││           ││ └─────────────┘ │
    └─────────┘└───────────┘└──────────────────┘
```

---

## ⚡ OPTIMIZACIONES IMPLEMENTADAS

### Queries Optimizadas

```python
# MALO: N+1 queries
for venta in Venta.objects.all():
    print(venta.cliente.nombre)  # Query por cada venta

# BUENO: Prefetch related
ventas = Venta.objects.select_related('cliente').all()
for venta in ventas:
    print(venta.cliente.nombre)  # Sin queries adicionales
```

### Agregaciones Eficientes

```python
# ORM Aggregation (1 query)
stats = Venta.objects.aggregate(
    total=Sum('total'),
    pagado=Sum('monto_pagado'),
    cantidad=Count('id')
)

# En lugar de: 3 queries separadas
```

### Transacciones Atómicas

```python
# Garantiza consistencia
with transaction.atomic():
    venta.save()
    for detalle in detalles:
        detalle.save()
    # Si algo falla → rollback automático
```

---

## 🎓 PATRONES DE DISEÑO UTILIZADOS

### 1. **Model-View-Form Pattern**
```
Model (Venta)    ← Define estructura
↓
Form (VentaForm) ← Valida datos
↓
View (ventas_form) ← Lógica negocio
↓
Template (ventas.html) ← Presentación
```

### 2. **DRY (Don't Repeat Yourself)**
```
recalcular_totales_venta() se llama desde:
- editar_venta()
- agregar_pago()
- eliminar_detalle()
```

### 3. **Single Responsibility**
```
- Form: solo validación
- View: solo lógica de negocio
- Template: solo presentación
```

### 4. **Transaction Safety**
```
transaction.atomic() envuelve:
- Creaciones
- Actualizaciones
- Cálculos
```

---

## 📈 FLUJO COMPLETO DE EJEMPLO

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Usuario accede a /ventas/                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 2. Renderiza VentaForm + lista de productos                │
│    Cliente: Valentina                                       │
│    Producto 1: Papa Primera, 30kg, $250k/kg                │
│    Producto 2: Rechazo, 20kg, $70k/kg                      │
│    Tipo: Crédito                                            │
│    Pagado: $1,000,000                                       │
│                                                              │
│ 3. POST /ventas/ con datos                                  │
│    form.is_valid() ✓                                        │
│                                                              │
│ 4. Crear Venta (total=$8,900k)                              │
│    ├─ Crear DetalleVenta (Papa: 30kg)                       │
│    └─ Crear DetalleVenta (Rechazo: 20kg)                    │
│                                                              │
│ 5. Redirect a /ventas/ con mensaje éxito                    │
│    "Venta a crédito registrada"                             │
│                                                              │
│ 6. Usuario va a /ventas/lista/                              │
│    Ve venta #33 con estado "pendiente"                      │
│                                                              │
│ 7. Click en "Ver" → /ventas/33/detalle/                     │
│    Ve todos los detalles, productos, totales                │
│                                                              │
│ 8. Click en "Editar Venta" → /ventas/33/editar/            │
│    Selecciona "Agregar nuevo producto"                      │
│    Producto: Tronco, 15kg, $80k/kg                          │
│    Click "Aplicar"                                          │
│                                                              │
│ 9. recalcular_totales_venta() se ejecuta                    │
│    Total: $8,900k → $9,100k                                │
│    Cantidad: 50kg → 65kg                                    │
│    Mensaje: "Producto agregado"                             │
│                                                              │
│ 10. Usuario regresa a detalle                               │
│     Click "Registrar Pago"                                  │
│     Ingresa $2,000,000                                      │
│                                                              │
│ 11. Crear Cobro($2,000,000)                                │
│     Actualizar Venta.monto_pagado                           │
│     actualizar_estado_pago()                                │
│     Saldo: $7,100,000                                       │
│     Estado: "pendiente"                                     │
│                                                              │
│ 12. Nuevo abono $7,100,000                                  │
│     Estado: "pagado" ✓                                      │
│     Mensaje: "¡VENTA COMPLETAMENTE PAGADA!"               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Documento actualizado**: 1 de mayo de 2026
**Versión**: 1.0 - Arquitectura Completa
