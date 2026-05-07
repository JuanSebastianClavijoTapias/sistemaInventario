"""
Suite de tests para el módulo de ventas.
Verifica que al registrar/editar una venta los valores queden
correctamente guardados en toda la aplicación.
"""
from decimal import Decimal
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from apps.clientes.models import Clientes
from apps.proveedores.models import Proveedores
from apps.productos.models import Productos
from apps.ventas.models import Venta, DetalleVenta, Cobro
from apps.ventas.views import recalcular_totales_venta
from panelprincipal.views import calcular_datos_semana


# ─── Helpers ────────────────────────────────────────────────────────────────

def crear_proveedor():
    return Proveedores.objects.create(nombre="Proveedor Test", telefono="3001234567")


def crear_producto(proveedor, nombre="Papa Primera", precio_compra=800, precio_venta=1200, stock=500):
    return Productos.objects.create(
        nombre=nombre,
        precio_compra=Decimal(str(precio_compra)),
        precio_venta=Decimal(str(precio_venta)),
        stock=stock,
        proveedor=proveedor,
    )


def crear_cliente():
    return Clientes.objects.create(nombre="Juan", apellido="Pérez")


def crear_venta_completa(cliente, producto, cantidad=10, precio_venta=1200):
    """Crea una venta de pago completo con su detalle y descuenta stock."""
    pc = Decimal(str(producto.precio_compra))
    pv = Decimal(str(precio_venta))
    subtotal = pv * cantidad
    ganancia = (pv - pc) * cantidad

    venta = Venta.objects.create(
        cliente=cliente,
        producto=producto,
        cantidad=cantidad,
        total=subtotal,
        precio_compra=pc,
        precio_venta=pv,
        ganancia=ganancia,
        tipo_pago='completo',
        monto_pagado=subtotal,
        estado_pago='pagado',
    )
    DetalleVenta.objects.create(
        venta=venta,
        producto=producto,
        cantidad=cantidad,
        precio_compra=pc,
        precio_venta=pv,
        subtotal=subtotal,
        ganancia=ganancia,
    )
    producto.stock -= cantidad
    producto.save()
    return venta


# ─── 1. Registro de venta via vista HTTP ─────────────────────────────────────

class RegistroVentaViewTest(TestCase):
    """Prueba el endpoint POST /ventas/ con datos reales."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, stock=200)
        self.cliente = crear_cliente()

    def _post_venta(self, cantidad=10, precio=1200, monto_efectivo=0, monto_transferencia=0):
        return self.client.post(reverse('ventas'), {
            'cliente': self.cliente.idCliente,
            'producto[]': [self.producto.idProducto],
            'cantidad[]': [str(cantidad)],
            'precio_venta[]': [str(precio)],
            'monto_efectivo': str(monto_efectivo),
            'monto_transferencia': str(monto_transferencia),
            'dias_credito': '15',
        })

    # ── 1.1 Pago completo ──
    def test_venta_completa_crea_registro_venta(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        self.assertEqual(Venta.objects.count(), 1)

    def test_venta_completa_crea_detalle_venta(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        self.assertEqual(DetalleVenta.objects.count(), 1)

    def test_venta_completa_total_correcto(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        v = Venta.objects.first()
        self.assertEqual(v.total, Decimal('12000'))

    def test_venta_completa_ganancia_correcta(self):
        # precio_compra=800, precio_venta=1200, cantidad=10 → ganancia=4000
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        v = Venta.objects.first()
        self.assertEqual(v.ganancia, Decimal('4000'))

    def test_venta_completa_monto_pagado_igual_total(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        v = Venta.objects.first()
        self.assertEqual(v.monto_pagado, v.total)

    def test_venta_completa_estado_pagado(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        v = Venta.objects.first()
        self.assertEqual(v.estado_pago, 'pagado')

    def test_venta_completa_tipo_pago_correcto(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        v = Venta.objects.first()
        self.assertEqual(v.tipo_pago, 'completo')

    def test_venta_completa_descuenta_stock(self):
        stock_inicial = self.producto.stock
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, stock_inicial - 10)

    def test_venta_completa_detalle_subtotal_correcto(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        d = DetalleVenta.objects.first()
        self.assertEqual(d.subtotal, Decimal('12000'))

    def test_venta_completa_detalle_ganancia_correcta(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=12000)
        d = DetalleVenta.objects.first()
        self.assertEqual(d.ganancia, Decimal('4000'))

    # ── 1.2 Venta a crédito ──
    def test_venta_fiado_estado_pendiente(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=0)
        v = Venta.objects.first()
        self.assertEqual(v.estado_pago, 'pendiente')
        self.assertEqual(v.tipo_pago, 'fiado')

    def test_venta_fiado_monto_pagado_cero(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=0)
        v = Venta.objects.first()
        self.assertEqual(v.monto_pagado, Decimal('0'))

    def test_venta_parcial_monto_pagado_correcto(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=5000)
        v = Venta.objects.first()
        self.assertEqual(v.monto_pagado, Decimal('5000'))

    def test_venta_sin_stock_suficiente_no_registra(self):
        self._post_venta(cantidad=9999, precio=1200, monto_efectivo=0)
        self.assertEqual(Venta.objects.count(), 0)

    def test_venta_monto_mayor_total_no_registra(self):
        self._post_venta(cantidad=10, precio=1200, monto_efectivo=99999)
        self.assertEqual(Venta.objects.count(), 0)


# ─── 2. Detalle de venta ──────────────────────────────────────────────────────

class DetalleVentaTest(TestCase):
    """Verifica la consistencia entre Venta y sus DetalleVenta."""

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.cliente = crear_cliente()

    def test_detalle_vinculado_a_venta(self):
        v = crear_venta_completa(self.cliente, self.producto)
        self.assertEqual(v.detalles.count(), 1)
        self.assertEqual(v.detalles.first().venta, v)

    def test_detalle_precio_compra_viene_del_producto(self):
        v = crear_venta_completa(self.cliente, self.producto)
        d = v.detalles.first()
        self.assertEqual(d.precio_compra, self.producto.precio_compra)

    def test_suma_subtotales_igual_total_venta(self):
        v = crear_venta_completa(self.cliente, self.producto, cantidad=15, precio_venta=1300)
        suma_subtotales = sum(d.subtotal for d in v.detalles.all())
        self.assertEqual(suma_subtotales, v.total)

    def test_suma_ganancias_igual_ganancia_venta(self):
        v = crear_venta_completa(self.cliente, self.producto, cantidad=15, precio_venta=1300)
        suma_ganancias = sum(d.ganancia for d in v.detalles.all())
        self.assertEqual(suma_ganancias, v.ganancia)


# ─── 3. Edición de venta ─────────────────────────────────────────────────────

class EditarVentaTest(TestCase):
    """Verifica que editar precio/cantidad actualiza toda la venta."""

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = Client()
        self.client.login(username='tester', password='pass')
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, precio_compra=800, precio_venta=1200)
        self.cliente = crear_cliente()
        self.venta = crear_venta_completa(self.cliente, self.producto, cantidad=10, precio_venta=1200)
        self.detalle = self.venta.detalles.first()

    def _editar(self, cantidad=None, precio=None):
        c = cantidad if cantidad is not None else self.detalle.cantidad
        p = precio if precio is not None else int(self.detalle.precio_venta)
        return self.client.post(reverse('editar_venta', args=[self.venta.idVenta]), {
            'accion_editar': 'actualizar',
            f'cantidad_{self.detalle.id}': str(c),
            f'precio_{self.detalle.id}': str(p),
        })

    def test_editar_cantidad_actualiza_total_venta(self):
        self._editar(cantidad=20, precio=1200)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.total, Decimal('24000'))

    def test_editar_precio_actualiza_total_venta(self):
        self._editar(cantidad=10, precio=1500)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.total, Decimal('15000'))

    def test_editar_actualiza_ganancia(self):
        # precio_compra=800, nuevo precio_venta=1500, cantidad=10 → ganancia=7000
        self._editar(cantidad=10, precio=1500)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.ganancia, Decimal('7000'))

    def test_editar_actualiza_detalle_subtotal(self):
        self._editar(cantidad=5, precio=1200)
        self.detalle.refresh_from_db()
        self.assertEqual(self.detalle.subtotal, Decimal('6000'))

    def test_editar_venta_completa_sincroniza_monto_pagado(self):
        """monto_pagado debe actualizarse igual al nuevo total en ventas completas."""
        self._editar(cantidad=10, precio=1500)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.monto_pagado, self.venta.total)

    def test_editar_venta_completa_mantiene_estado_pagado(self):
        self._editar(cantidad=10, precio=1500)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.estado_pago, 'pagado')

    def test_editar_actualiza_cantidad_venta(self):
        self._editar(cantidad=25, precio=1200)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.cantidad, 25)


# ─── 4. Recalcular totales (función auxiliar) ────────────────────────────────

class RecalcularTotalesTest(TestCase):
    """Prueba directa de la función recalcular_totales_venta."""

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, precio_compra=500, precio_venta=900)
        self.cliente = crear_cliente()
        self.venta = crear_venta_completa(self.cliente, self.producto, cantidad=10, precio_venta=900)

    def test_recalculo_con_nuevo_precio(self):
        d = self.venta.detalles.first()
        d.precio_venta = Decimal('1100')
        d.subtotal = Decimal('1100') * d.cantidad
        d.ganancia = (Decimal('1100') - d.precio_compra) * d.cantidad
        d.save()
        recalcular_totales_venta(self.venta)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.total, Decimal('11000'))
        self.assertEqual(self.venta.ganancia, Decimal('6000'))

    def test_recalculo_venta_completa_sincroniza_monto_pagado(self):
        d = self.venta.detalles.first()
        d.precio_venta = Decimal('2000')
        d.subtotal = Decimal('2000') * d.cantidad
        d.ganancia = (Decimal('2000') - d.precio_compra) * d.cantidad
        d.save()
        recalcular_totales_venta(self.venta)
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.monto_pagado, Decimal('20000'))
        self.assertEqual(self.venta.monto_pagado, self.venta.total)

    def test_recalculo_multiple_detalles(self):
        producto2 = crear_producto(self.proveedor, nombre="Tronco", precio_compra=300, precio_venta=600, stock=200)
        DetalleVenta.objects.create(
            venta=self.venta,
            producto=producto2,
            cantidad=5,
            precio_compra=Decimal('300'),
            precio_venta=Decimal('600'),
            subtotal=Decimal('3000'),
            ganancia=Decimal('1500'),
        )
        recalcular_totales_venta(self.venta)
        self.venta.refresh_from_db()
        # 10*900 + 5*600 = 9000 + 3000 = 12000
        self.assertEqual(self.venta.total, Decimal('12000'))
        # (900-500)*10 + (600-300)*5 = 4000 + 1500 = 5500
        self.assertEqual(self.venta.ganancia, Decimal('5500'))


# ─── 5. Cobros / pagos de créditos ───────────────────────────────────────────

class CobroVentaTest(TestCase):
    """Verifica el registro de cobros en ventas a crédito."""

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = Client()
        self.client.login(username='tester', password='pass')
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.cliente = crear_cliente()
        # Venta a crédito por $12000, no pagada
        self.venta = Venta.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=10,
            total=Decimal('12000'),
            precio_compra=Decimal('800'),
            precio_venta=Decimal('1200'),
            ganancia=Decimal('4000'),
            tipo_pago='fiado',
            monto_pagado=Decimal('0'),
            estado_pago='pendiente',
        )

    def test_cobro_parcial_actualiza_monto_pagado(self):
        self.client.post(reverse('agregar_pago', args=[self.venta.idVenta]), {
            'monto': '5000',
        })
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.monto_pagado, Decimal('5000'))

    def test_cobro_total_cambia_estado_a_pagado(self):
        self.client.post(reverse('agregar_pago', args=[self.venta.idVenta]), {
            'monto': '12000',
        })
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.estado_pago, 'pagado')

    def test_cobro_crea_registro_cobro(self):
        self.client.post(reverse('agregar_pago', args=[self.venta.idVenta]), {
            'monto': '3000',
        })
        self.assertEqual(Cobro.objects.filter(venta=self.venta).count(), 1)

    def test_cobro_saldo_pendiente_correcto(self):
        self.client.post(reverse('agregar_pago', args=[self.venta.idVenta]), {
            'monto': '7000',
        })
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.saldo_pendiente, Decimal('5000'))


# ─── 6. Stock de productos ────────────────────────────────────────────────────

class StockProductoTest(TestCase):
    """Verifica que el stock se gestiona correctamente."""

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = Client()
        self.client.login(username='tester', password='pass')
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, stock=100)
        self.cliente = crear_cliente()

    def test_stock_disminuye_al_registrar_venta(self):
        self.client.post(reverse('ventas'), {
            'cliente': self.cliente.idCliente,
            'producto[]': [self.producto.idProducto],
            'cantidad[]': ['30'],
            'precio_venta[]': ['1200'],
            'monto_efectivo': '36000',
            'monto_transferencia': '0',
            'dias_credito': '15',
        })
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 70)

    def test_stock_no_negativo_con_venta_excedente(self):
        self.client.post(reverse('ventas'), {
            'cliente': self.cliente.idCliente,
            'producto[]': [self.producto.idProducto],
            'cantidad[]': ['200'],
            'precio_venta[]': ['1200'],
            'monto_efectivo': '240000',
            'monto_transferencia': '0',
            'dias_credito': '15',
        })
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 100)  # no debió cambiar


# ─── 7. Resumen semanal (panel principal) ─────────────────────────────────────

class ResumenSemanalTest(TestCase):
    """Verifica que calcular_datos_semana refleja ventas y ediciones."""

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor, precio_compra=800, precio_venta=1200)
        self.cliente = crear_cliente()
        self.hoy = timezone.localdate()

    def test_total_ingresos_suma_ventas_del_dia(self):
        crear_venta_completa(self.cliente, self.producto, cantidad=10, precio_venta=1200)
        crear_venta_completa(self.cliente, self.producto, cantidad=5, precio_venta=1000)
        datos = calcular_datos_semana(self.hoy, self.hoy)
        self.assertEqual(datos['total_ingresos'], Decimal('17000'))

    def test_total_recaudado_venta_completa(self):
        crear_venta_completa(self.cliente, self.producto, cantidad=10, precio_venta=1200)
        datos = calcular_datos_semana(self.hoy, self.hoy)
        self.assertEqual(datos['total_recaudado'], Decimal('12000'))

    def test_total_recaudado_venta_fiado_cero(self):
        Venta.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=10,
            total=Decimal('12000'),
            precio_compra=Decimal('800'),
            precio_venta=Decimal('1200'),
            ganancia=Decimal('4000'),
            tipo_pago='fiado',
            monto_pagado=Decimal('0'),
            estado_pago='pendiente',
        )
        datos = calcular_datos_semana(self.hoy, self.hoy)
        self.assertEqual(datos['total_recaudado'], Decimal('0'))

    def test_total_ganancia_suma_correcta(self):
        # ganancia = (1200-800)*10 = 4000
        crear_venta_completa(self.cliente, self.producto, cantidad=10, precio_venta=1200)
        datos = calcular_datos_semana(self.hoy, self.hoy)
        self.assertEqual(datos['total_ganancia'], Decimal('4000'))

    def test_resumen_refleja_edicion_precio(self):
        """Después de editar el precio, el resumen debe reflejar el nuevo total."""
        venta = crear_venta_completa(self.cliente, self.producto, cantidad=10, precio_venta=1200)
        # Editar precio manualmente (como hace la vista)
        d = venta.detalles.first()
        d.precio_venta = Decimal('1500')
        d.subtotal = Decimal('1500') * d.cantidad
        d.ganancia = (Decimal('1500') - d.precio_compra) * d.cantidad
        d.save()
        recalcular_totales_venta(venta)
        datos = calcular_datos_semana(self.hoy, self.hoy)
        self.assertEqual(datos['total_ingresos'], Decimal('15000'))
        self.assertEqual(datos['total_recaudado'], Decimal('15000'))  # monto_pagado sincronizado

    def test_cantidad_ventas_correcta(self):
        crear_venta_completa(self.cliente, self.producto, cantidad=10)
        crear_venta_completa(self.cliente, self.producto, cantidad=5)
        datos = calcular_datos_semana(self.hoy, self.hoy)
        self.assertEqual(datos['cantidad_ventas'], 2)

    def test_ventas_fuera_de_rango_no_cuentan(self):
        """Ventas de hace más de un año no deben aparecer en el resumen de hoy."""
        from datetime import timedelta
        crear_venta_completa(self.cliente, self.producto, cantidad=10)
        ayer = self.hoy - timedelta(days=365)
        datos = calcular_datos_semana(ayer - timedelta(days=1), ayer)
        self.assertEqual(datos['total_ingresos'], 0)


# ─── 8. Modelo Venta – propiedades y métodos ─────────────────────────────────

class VentaModelTest(TestCase):

    def setUp(self):
        self.proveedor = crear_proveedor()
        self.producto = crear_producto(self.proveedor)
        self.cliente = crear_cliente()

    def test_saldo_pendiente_correcto(self):
        v = Venta.objects.create(
            cliente=self.cliente, producto=self.producto,
            cantidad=10, total=Decimal('12000'),
            precio_compra=Decimal('800'), precio_venta=Decimal('1200'),
            ganancia=Decimal('4000'), tipo_pago='fiado',
            monto_pagado=Decimal('5000'), estado_pago='pendiente',
        )
        self.assertEqual(v.saldo_pendiente, Decimal('7000'))

    def test_actualizar_estado_pago_cuando_pagado_total(self):
        v = Venta.objects.create(
            cliente=self.cliente, producto=self.producto,
            cantidad=10, total=Decimal('12000'),
            precio_compra=Decimal('800'), precio_venta=Decimal('1200'),
            ganancia=Decimal('4000'), tipo_pago='fiado',
            monto_pagado=Decimal('12000'), estado_pago='pendiente',
        )
        v.actualizar_estado_pago()
        v.refresh_from_db()
        self.assertEqual(v.estado_pago, 'pagado')

    def test_venta_completa_siempre_pagado(self):
        v = Venta.objects.create(
            cliente=self.cliente, producto=self.producto,
            cantidad=10, total=Decimal('12000'),
            precio_compra=Decimal('800'), precio_venta=Decimal('1200'),
            ganancia=Decimal('4000'), tipo_pago='completo',
            monto_pagado=Decimal('12000'), estado_pago='pagado',
        )
        v.actualizar_estado_pago()
        self.assertEqual(v.estado_pago, 'pagado')

