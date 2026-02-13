// ==================== DATOS ====================
let proveedores = [];
let filtroActual = 'todos';

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarDatos();
    actualizarLista();
    actualizarResumen();
    
    // Event listeners
    document.getElementById('formProveedores').addEventListener('submit', agregarProveedor);
    document.getElementById('proveedorCompra').addEventListener('input', calcularSaldo);
    document.getElementById('proveedorInicial').addEventListener('input', calcularSaldo);
});

// ==================== FUNCIONES PRINCIPALES ====================
function agregarProveedor(e) {
    e.preventDefault();
    
    const compra = parseFloat(document.getElementById('proveedorCompra').value);
    const inicial = parseFloat(document.getElementById('proveedorInicial').value);
    const tipo = document.getElementById('proveedorTipo').value;
    
    // Validar que el inicial no sea mayor que la compra
    if (inicial > compra) {
        alert('El pago inicial no puede ser mayor que el monto de compra');
        return;
    }
    
    const proveedor = {
        id: Date.now(),
        nombre: document.getElementById('proveedorNombre').value,
        telefono: document.getElementById('proveedorTelefono').value,
        descripcion: document.getElementById('proveedorDescripcion').value,
        compra: compra,
        inicial: inicial,
        tipo: tipo,
        saldo: compra - inicial,
        fecha: new Date().toISOString().split('T')[0],
        abonos: []
    };
    
    proveedores.unshift(proveedor);
    guardarDatos();
    actualizarLista();
    actualizarResumen();
    limpiarFormulario();
    
    mostrarNotificacion('Proveedor registrado exitosamente');
}

function eliminarRegistro(id) {
    if (confirm('¿Estás seguro de eliminar este proveedor?')) {
        proveedores = proveedores.filter(p => p.id !== id);
        guardarDatos();
        actualizarLista();
        actualizarResumen();
        mostrarNotificacion('Proveedor eliminado');
    }
}

function agregarAbono(id) {
    const proveedor = proveedores.find(p => p.id === id);
    if (!proveedor) return;
    
    const monto = parseFloat(prompt(`Ingrese el monto del pago para ${proveedor.nombre}:\nSaldo pendiente: ${formatearMoneda(proveedor.saldo)}`));
    
    if (isNaN(monto) || monto <= 0) {
        alert('Ingrese un monto válido');
        return;
    }
    
    if (monto > proveedor.saldo) {
        alert('El pago no puede ser mayor que el saldo pendiente');
        return;
    }
    
    // Agregar abono
    proveedor.abonos.push({
        monto: monto,
        fecha: new Date().toISOString().split('T')[0]
    });
    proveedor.saldo -= monto;
    proveedor.inicial += monto;
    
    // Si ya pagó todo, cambiar a completa
    if (proveedor.saldo <= 0) {
        proveedor.tipo = 'completa';
        proveedor.saldo = 0;
    }
    
    guardarDatos();
    actualizarLista();
    actualizarResumen();
    mostrarNotificacion('Pago registrado exitosamente');
}

function buscar() {
    const input = document.getElementById('buscarProveedores').value.toLowerCase();
    const items = document.querySelectorAll('.registro-item');
    
    items.forEach(item => {
        const texto = item.textContent.toLowerCase();
        const matchBusqueda = texto.includes(input);
        const matchFiltro = filtroActual === 'todos' || item.dataset.tipo === filtroActual;
        item.style.display = (matchBusqueda && matchFiltro) ? 'block' : 'none';
    });
}

function filtrar(tipo) {
    filtroActual = tipo;
    
    // Actualizar botones
    document.querySelectorAll('.filtro-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Aplicar filtro
    const items = document.querySelectorAll('.registro-item');
    items.forEach(item => {
        if (tipo === 'todos') {
            item.style.display = 'block';
        } else {
            item.style.display = item.dataset.tipo === tipo ? 'block' : 'none';
        }
    });
}

function actualizarTipoCompra() {
    const tipo = document.getElementById('proveedorTipo').value;
    const rowSaldo = document.getElementById('rowSaldo');
    
    if (tipo === 'fiada') {
        rowSaldo.style.display = 'block';
        calcularSaldo();
    } else {
        rowSaldo.style.display = 'none';
        // Si es completa, el inicial debe ser igual a la compra
        const compra = document.getElementById('proveedorCompra').value;
        document.getElementById('proveedorInicial').value = compra;
    }
}

function calcularSaldo() {
    const compra = parseFloat(document.getElementById('proveedorCompra').value) || 0;
    const inicial = parseFloat(document.getElementById('proveedorInicial').value) || 0;
    const saldo = compra - inicial;
    
    document.getElementById('saldoPendiente').textContent = formatearMoneda(Math.max(0, saldo));
}

// ==================== ACTUALIZACIÓN DE UI ====================
function actualizarLista() {
    const lista = document.getElementById('listaProveedores');
    
    if (proveedores.length === 0) {
        lista.innerHTML = '<p class="empty-message">No hay proveedores registrados</p>';
        return;
    }
    
    lista.innerHTML = proveedores.map(proveedor => `
        <div class="registro-item" data-id="${proveedor.id}" data-tipo="${proveedor.tipo}">
            <div class="registro-header">
                <span class="registro-titulo">${proveedor.nombre}</span>
                <div class="registro-acciones">
                    <span class="badge ${proveedor.tipo === 'completa' ? 'badge-completa' : 'badge-fiada'}">
                        ${proveedor.tipo === 'completa' ? 'Pagado' : 'Debo'}
                    </span>
                    ${proveedor.saldo > 0 ? `
                        <button class="btn-abono" onclick="agregarAbono(${proveedor.id})" title="Hacer pago">
                            <i class="fas fa-money-bill-wave"></i>
                        </button>
                    ` : ''}
                    <button class="btn-eliminar" onclick="eliminarRegistro(${proveedor.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="registro-detalles">
                ${proveedor.telefono ? `<span><i class="fas fa-phone"></i> ${proveedor.telefono}</span>` : ''}
                <span><i class="fas fa-box"></i> ${proveedor.descripcion}</span>
                <span><i class="fas fa-receipt"></i> Compra: ${formatearMoneda(proveedor.compra)}</span>
                <span><i class="fas fa-hand-holding-usd"></i> Pagado: ${formatearMoneda(proveedor.inicial)}</span>
                ${proveedor.saldo > 0 ? `
                    <span class="badge-pendiente deuda">
                        <i class="fas fa-exclamation-circle"></i> Debo: ${formatearMoneda(proveedor.saldo)}
                    </span>
                ` : ''}
            </div>
            <div class="registro-fecha-small">
                <i class="fas fa-calendar"></i> Registrado: ${formatearFecha(proveedor.fecha)}
            </div>
        </div>
    `).join('');
}

function actualizarResumen() {
    const totalProveedores = proveedores.length;
    const totalPorPagar = proveedores.reduce((sum, p) => sum + p.saldo, 0);
    const totalPagado = proveedores.reduce((sum, p) => sum + p.inicial, 0);
    
    document.getElementById('totalProveedores').textContent = totalProveedores;
    document.getElementById('totalPorPagar').textContent = formatearMoneda(totalPorPagar);
    document.getElementById('totalPagado').textContent = formatearMoneda(totalPagado);
}

// ==================== ALMACENAMIENTO ====================
function guardarDatos() {
    localStorage.setItem('inventario_proveedores', JSON.stringify(proveedores));
}

function cargarDatos() {
    const datos = localStorage.getItem('inventario_proveedores');
    if (datos) {
        proveedores = JSON.parse(datos);
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
    document.getElementById('formProveedores').reset();
    document.getElementById('rowSaldo').style.display = 'none';
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
