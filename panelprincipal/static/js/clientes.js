// ==================== DATOS ====================
let clientes = [];
let ventas = [];

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarDatos();
    cargarVentas();
    actualizarLista();
    actualizarResumen();
    
    // Event listener del formulario
    document.getElementById('formClientes').addEventListener('submit', agregarCliente);
    
    // Cerrar modal al hacer clic fuera
    document.getElementById('modalCliente').addEventListener('click', function(e) {
        if (e.target === this) {
            cerrarModal();
        }
    });
});

// ==================== FUNCIONES DE VENTAS ====================
function cargarVentas() {
    const datos = localStorage.getItem('inventario_ventas');
    if (datos) {
        ventas = JSON.parse(datos);
    }
}

// ==================== FUNCIONES PRINCIPALES ====================
function agregarCliente(e) {
    e.preventDefault();
    
    const cliente = {
        id: Date.now(),
        nombre: document.getElementById('clienteNombre').value,
        telefono: document.getElementById('clienteTelefono').value,
        fecha: new Date().toISOString().split('T')[0]
    };
    
    clientes.unshift(cliente);
    guardarDatos();
    actualizarLista();
    actualizarResumen();
    limpiarFormulario();
    
    mostrarNotificacion('Cliente agregado exitosamente');
}

function eliminarRegistro(id) {
    if (confirm('¿Estás seguro de eliminar este cliente?')) {
        clientes = clientes.filter(c => c.id !== id);
        guardarDatos();
        actualizarLista();
        actualizarResumen();
        mostrarNotificacion('Cliente eliminado');
    }
}

function buscar() {
    const input = document.getElementById('buscarClientes').value.toLowerCase();
    const items = document.querySelectorAll('.registro-item');
    
    items.forEach(item => {
        const texto = item.textContent.toLowerCase();
        item.style.display = texto.includes(input) ? 'block' : 'none';
    });
}

// ==================== ACTUALIZACIÓN DE UI ====================
function actualizarLista() {
    const lista = document.getElementById('listaClientes');
    
    if (clientes.length === 0) {
        lista.innerHTML = '<p class="empty-message">No hay clientes registrados</p>';
        return;
    }
    
    lista.innerHTML = clientes.map(cliente => {
        const ventasCliente = ventas.filter(v => v.clienteId == cliente.id);
        const totalDeuda = ventasCliente.reduce((sum, v) => sum + (v.saldo || 0), 0);
        
        return `
        <div class="registro-item registro-clickeable" data-id="${cliente.id}" onclick="verDetallesCliente(${cliente.id})">
            <div class="registro-header">
                <span class="registro-titulo">${cliente.nombre}</span>
                <div class="registro-acciones">
                    ${totalDeuda > 0 ? `<span class="badge badge-fiada">Debe: ${formatearMoneda(totalDeuda)}</span>` : '<span class="badge badge-completa">Sin deuda</span>'}
                    <button class="btn-eliminar" onclick="event.stopPropagation(); eliminarRegistro(${cliente.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="registro-detalles">
                ${cliente.telefono ? `<span><i class="fas fa-phone"></i> ${cliente.telefono}</span>` : '<span><i class="fas fa-phone"></i> Sin teléfono</span>'}
                <span><i class="fas fa-shopping-bag"></i> ${ventasCliente.length} compra(s)</span>
            </div>
            <div class="registro-fecha-small">
                <i class="fas fa-calendar"></i> Registrado: ${formatearFecha(cliente.fecha)}
            </div>
        </div>
    `;
    }).join('');
}

function actualizarResumen() {
    const totalClientes = clientes.length;
    document.getElementById('totalClientes').textContent = totalClientes;
}

// ==================== ALMACENAMIENTO ====================
function guardarDatos() {
    localStorage.setItem('inventario_clientes', JSON.stringify(clientes));
}

function cargarDatos() {
    const datos = localStorage.getItem('inventario_clientes');
    if (datos) {
        clientes = JSON.parse(datos);
    }
}

// ==================== FUNCIONES AUXILIARES ====================
function formatearFecha(fecha) {
    const opciones = { day: '2-digit', month: 'short', year: 'numeric' };
    return new Date(fecha + 'T00:00:00').toLocaleDateString('es-ES', opciones);
}

function formatearMoneda(valor) {
    return '$' + valor.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function limpiarFormulario() {
    document.getElementById('formClientes').reset();
}

// ==================== FUNCIONES DEL MODAL ====================
function verDetallesCliente(id) {
    cargarVentas(); // Recargar ventas por si hay nuevas
    
    const cliente = clientes.find(c => c.id === id);
    if (!cliente) return;
    
    // Filtrar ventas del cliente
    const ventasCliente = ventas.filter(v => v.clienteId == id);
    
    // Calcular totales
    const totalCompras = ventasCliente.reduce((sum, v) => sum + v.total, 0);
    const totalPagado = ventasCliente.reduce((sum, v) => sum + (v.abono || v.total), 0);
    const totalDeuda = ventasCliente.reduce((sum, v) => sum + (v.saldo || 0), 0);
    
    // Llenar información del modal
    document.getElementById('modalClienteNombre').textContent = cliente.nombre;
    document.getElementById('modalClienteTelefono').textContent = cliente.telefono || 'Sin teléfono';
    document.getElementById('modalClienteFecha').textContent = formatearFecha(cliente.fecha);
    document.getElementById('modalTotalCompras').textContent = formatearMoneda(totalCompras);
    document.getElementById('modalTotalPagado').textContent = formatearMoneda(totalPagado);
    document.getElementById('modalTotalDeuda').textContent = formatearMoneda(totalDeuda);
    
    // Aplicar color según deuda
    const deudaElement = document.getElementById('modalTotalDeuda');
    if (totalDeuda > 0) {
        deudaElement.style.color = '#e53935';
    } else {
        deudaElement.style.color = '#43a047';
    }
    
    // Llenar lista de compras
    const listaCompras = document.getElementById('listaComprasCliente');
    if (ventasCliente.length === 0) {
        listaCompras.innerHTML = '<p class="empty-message">Este cliente no tiene compras registradas</p>';
    } else {
        listaCompras.innerHTML = ventasCliente.map(venta => `
            <div class="compra-item ${(venta.tipo || 'completa') === 'fiada' ? 'compra-fiada' : 'compra-pagada'}">
                <div class="compra-header">
                    <span class="compra-producto">${venta.producto}</span>
                    <span class="badge ${(venta.tipo || 'completa') === 'completa' ? 'badge-completa' : 'badge-fiada'}">
                        ${(venta.tipo || 'completa') === 'completa' ? 'Pagado' : 'Fiado'}
                    </span>
                </div>
                <div class="compra-detalles">
                    <span><i class="fas fa-calendar"></i> ${formatearFecha(venta.fecha)}</span>
                    <span><i class="fas fa-boxes"></i> Cant: ${venta.cantidad}</span>
                    <span><i class="fas fa-tag"></i> ${formatearMoneda(venta.precio)}</span>
                </div>
                <div class="compra-totales">
                    <span><i class="fas fa-receipt"></i> Total: ${formatearMoneda(venta.total)}</span>
                    <span><i class="fas fa-hand-holding-usd"></i> Pagado: ${formatearMoneda(venta.abono || venta.total)}</span>
                    ${(venta.saldo || 0) > 0 ? `<span class="deuda"><i class="fas fa-exclamation-circle"></i> Debe: ${formatearMoneda(venta.saldo)}</span>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    // Mostrar modal
    document.getElementById('modalCliente').classList.add('active');
}

function cerrarModal() {
    document.getElementById('modalCliente').classList.remove('active');
}

function mostrarNotificacion(mensaje) {
    const notif = document.createElement('div');
    notif.className = 'notificacion';
    notif.innerHTML = `<i class="fas fa-check-circle"></i> ${mensaje}`;
    document.body.appendChild(notif);
    
    setTimeout(() => notif.classList.add('show'), 100);
    
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 2500);
}
