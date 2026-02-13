// ==================== DATOS ====================
let ventas = [];
let clientes = [];

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarDatos();
    cargarClientes();
    actualizarLista();
    actualizarResumen();
    
    // Establecer fecha actual
    document.getElementById('ventaFecha').value = new Date().toISOString().split('T')[0];
    
    // Event listener del formulario
    document.getElementById('formVentas').addEventListener('submit', agregarVenta);
    
    // Event listeners para calcular saldo dinámicamente
    document.getElementById('ventaCantidad').addEventListener('input', actualizarCalculos);
    document.getElementById('ventaPrecio').addEventListener('input', actualizarCalculos);
    document.getElementById('ventaAbono').addEventListener('input', calcularSaldoVenta);
});

function actualizarCalculos() {
    const tipo = document.getElementById('ventaTipo').value;
    if (tipo === 'completa') {
        calcularTotalVenta();
    } else if (tipo === 'fiada') {
        calcularSaldoVenta();
    }
}

// ==================== FUNCIONES DE CLIENTES ====================
function cargarClientes() {
    const datos = localStorage.getItem('inventario_clientes');
    if (datos) {
        clientes = JSON.parse(datos);
    }
    actualizarSelectClientes();
}

function actualizarSelectClientes() {
    const select = document.getElementById('ventaCliente');
    select.innerHTML = '<option value="">Seleccionar cliente...</option>';
    
    clientes.forEach(cliente => {
        const option = document.createElement('option');
        option.value = cliente.id;
        option.textContent = cliente.nombre;
        select.appendChild(option);
    });
}

// ==================== FUNCIONES PRINCIPALES ====================
function agregarVenta(e) {
    e.preventDefault();
    
    const clienteId = document.getElementById('ventaCliente').value;
    const cliente = clientes.find(c => c.id == clienteId);
    const cantidad = parseInt(document.getElementById('ventaCantidad').value);
    const precio = parseFloat(document.getElementById('ventaPrecio').value);
    const total = cantidad * precio;
    const tipo = document.getElementById('ventaTipo').value;
    const abono = parseFloat(document.getElementById('ventaAbono').value) || 0;
    
    // Validar que el abono no sea mayor que el total
    if (abono > total) {
        alert('El abono inicial no puede ser mayor que el total de la venta');
        return;
    }
    
    const venta = {
        id: Date.now(),
        clienteId: clienteId,
        clienteNombre: cliente ? cliente.nombre : 'Sin cliente',
        producto: document.getElementById('ventaProducto').value,
        cantidad: cantidad,
        precio: precio,
        fecha: document.getElementById('ventaFecha').value,
        total: total,
        tipo: tipo,
        abono: abono,
        saldo: total - abono,
        abonos: []
    };
    
    ventas.unshift(venta);
    guardarDatos();
    actualizarLista();
    actualizarResumen();
    limpiarFormulario();
    
    // Mostrar notificación
    mostrarNotificacion('Venta registrada exitosamente');
}

function actualizarTipoPago() {
    const tipo = document.getElementById('ventaTipo').value;
    const groupSaldo = document.getElementById('groupSaldo');
    
    if (tipo === 'fiada') {
        groupSaldo.style.display = 'block';
        calcularSaldoVenta();
    } else if (tipo === 'completa') {
        groupSaldo.style.display = 'none';
        // Si es pago completo, el abono debe ser igual al total
        calcularTotalVenta();
    } else {
        groupSaldo.style.display = 'none';
    }
}

function calcularTotalVenta() {
    const cantidad = parseInt(document.getElementById('ventaCantidad').value) || 0;
    const precio = parseFloat(document.getElementById('ventaPrecio').value) || 0;
    const total = cantidad * precio;
    document.getElementById('ventaAbono').value = total.toFixed(2);
}

function calcularSaldoVenta() {
    const cantidad = parseInt(document.getElementById('ventaCantidad').value) || 0;
    const precio = parseFloat(document.getElementById('ventaPrecio').value) || 0;
    const abono = parseFloat(document.getElementById('ventaAbono').value) || 0;
    const total = cantidad * precio;
    const saldo = total - abono;
    
    document.getElementById('saldoPendiente').textContent = formatearMoneda(Math.max(0, saldo));
}

function agregarAbonoVenta(id) {
    const venta = ventas.find(v => v.id === id);
    if (!venta) return;
    
    const monto = parseFloat(prompt(`Ingrese el monto del abono para la venta de ${venta.clienteNombre}:\nSaldo pendiente: ${formatearMoneda(venta.saldo)}`));
    
    if (isNaN(monto) || monto <= 0) {
        alert('Ingrese un monto válido');
        return;
    }
    
    if (monto > venta.saldo) {
        alert('El abono no puede ser mayor que el saldo pendiente');
        return;
    }
    
    // Agregar abono
    venta.abonos.push({
        monto: monto,
        fecha: new Date().toISOString().split('T')[0]
    });
    venta.saldo -= monto;
    venta.abono += monto;
    
    // Si ya pagó todo, cambiar a completa
    if (venta.saldo <= 0) {
        venta.tipo = 'completa';
        venta.saldo = 0;
    }
    
    guardarDatos();
    actualizarLista();
    actualizarResumen();
    mostrarNotificacion('Abono registrado exitosamente');
}

function eliminarRegistro(id) {
    if (confirm('¿Estás seguro de eliminar esta venta?')) {
        ventas = ventas.filter(v => v.id !== id);
        guardarDatos();
        actualizarLista();
        actualizarResumen();
        mostrarNotificacion('Venta eliminada');
    }
}

function buscar() {
    const input = document.getElementById('buscarVentas').value.toLowerCase();
    const items = document.querySelectorAll('.registro-item');
    
    items.forEach(item => {
        const texto = item.textContent.toLowerCase();
        item.style.display = texto.includes(input) ? 'block' : 'none';
    });
}

// ==================== ACTUALIZACIÓN DE UI ====================
function actualizarLista() {
    const lista = document.getElementById('listaVentas');
    
    if (ventas.length === 0) {
        lista.innerHTML = '<p class="empty-message">No hay ventas registradas</p>';
        return;
    }
    
    lista.innerHTML = ventas.map(venta => `
        <div class="registro-item" data-id="${venta.id}" data-tipo="${venta.tipo || 'completa'}">
            <div class="registro-header">
                <span class="registro-titulo">${venta.producto}</span>
                <div class="registro-acciones">
                    <span class="badge ${(venta.tipo || 'completa') === 'completa' ? 'badge-completa' : 'badge-fiada'}">
                        ${(venta.tipo || 'completa') === 'completa' ? 'Pagado' : 'Fiado'}
                    </span>
                    ${(venta.saldo || 0) > 0 ? `
                        <button class="btn-abono" onclick="agregarAbonoVenta(${venta.id})" title="Agregar abono">
                            <i class="fas fa-money-bill-wave"></i>
                        </button>
                    ` : ''}
                    <button class="btn-eliminar" onclick="eliminarRegistro(${venta.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="registro-detalles">
                <span><i class="fas fa-user"></i> Cliente: ${venta.clienteNombre || 'Sin cliente'}</span>
                <span><i class="fas fa-boxes"></i> Cantidad: ${venta.cantidad}</span>
                <span><i class="fas fa-tag"></i> Precio: ${formatearMoneda(venta.precio)}</span>
                <span class="registro-monto"><i class="fas fa-dollar-sign"></i> Total: ${formatearMoneda(venta.total)}</span>
            </div>
            <div class="registro-detalles">
                <span><i class="fas fa-hand-holding-usd"></i> Abonado: ${formatearMoneda(venta.abono || venta.total)}</span>
                ${(venta.saldo || 0) > 0 ? `
                    <span class="badge-pendiente">
                        <i class="fas fa-exclamation-circle"></i> Debe: ${formatearMoneda(venta.saldo)}
                    </span>
                ` : ''}
            </div>
            <div class="registro-fecha-small">
                <i class="fas fa-calendar"></i> ${formatearFecha(venta.fecha)}
            </div>
        </div>
    `).join('');
}

function actualizarResumen() {
    const hoy = new Date().toISOString().split('T')[0];
    const ventasHoy = ventas.filter(v => v.fecha === hoy);
    const totalHoy = ventasHoy.reduce((sum, v) => sum + v.total, 0);
    const totalPorCobrar = ventas.reduce((sum, v) => sum + (v.saldo || 0), 0);
    
    document.getElementById('totalVentasDia').textContent = formatearMoneda(totalHoy);
    document.getElementById('cantidadVentasHoy').textContent = ventasHoy.length;
    document.getElementById('totalPorCobrar').textContent = formatearMoneda(totalPorCobrar);
}

// ==================== ALMACENAMIENTO ====================
function guardarDatos() {
    localStorage.setItem('inventario_ventas', JSON.stringify(ventas));
}

function cargarDatos() {
    const datos = localStorage.getItem('inventario_ventas');
    if (datos) {
        ventas = JSON.parse(datos);
    }
}

// ==================== FUNCIONES AUXILIARES ====================
function formatearMoneda(valor) {
    return '$' + valor.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatearFecha(fecha) {
    const opciones = { day: '2-digit', month: 'short', year: 'numeric' };
    return new Date(fecha + 'T00:00:00').toLocaleDateString('es-ES', opciones);
}

function limpiarFormulario() {
    document.getElementById('formVentas').reset();
    document.getElementById('ventaFecha').value = new Date().toISOString().split('T')[0];
    document.getElementById('ventaCliente').value = '';
    document.getElementById('ventaTipo').value = '';
    document.getElementById('ventaAbono').value = '';
    document.getElementById('groupSaldo').style.display = 'none';
}

function mostrarNotificacion(mensaje) {
    // Crear notificación
    const notif = document.createElement('div');
    notif.className = 'notificacion';
    notif.innerHTML = `<i class="fas fa-check-circle"></i> ${mensaje}`;
    document.body.appendChild(notif);
    
    // Mostrar
    setTimeout(() => notif.classList.add('show'), 100);
    
    // Ocultar y eliminar
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 2500);
}
