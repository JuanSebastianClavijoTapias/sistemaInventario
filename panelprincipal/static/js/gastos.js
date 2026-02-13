// ==================== DATOS ====================
let gastos = [];
let filtroActual = 'todos';

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarDatos();
    actualizarLista();
    actualizarResumen();
    
    // Establecer fecha actual
    document.getElementById('gastoFecha').value = new Date().toISOString().split('T')[0];
    
    // Event listener del formulario
    document.getElementById('formGastos').addEventListener('submit', agregarGasto);
});

// ==================== FUNCIONES PRINCIPALES ====================
function agregarGasto(e) {
    e.preventDefault();
    
    const gasto = {
        id: Date.now(),
        descripcion: document.getElementById('gastoDescripcion').value,
        categoria: document.getElementById('gastoCategoria').value,
        monto: parseFloat(document.getElementById('gastoMonto').value),
        fecha: document.getElementById('gastoFecha').value
    };
    
    gastos.unshift(gasto);
    guardarDatos();
    actualizarLista();
    actualizarResumen();
    limpiarFormulario();
    
    mostrarNotificacion('Gasto registrado exitosamente');
}

function eliminarRegistro(id) {
    if (confirm('¿Estás seguro de eliminar este gasto?')) {
        gastos = gastos.filter(g => g.id !== id);
        guardarDatos();
        actualizarLista();
        actualizarResumen();
        mostrarNotificacion('Gasto eliminado');
    }
}

function buscar() {
    const input = document.getElementById('buscarGastos').value.toLowerCase();
    const items = document.querySelectorAll('.registro-item');
    
    items.forEach(item => {
        const texto = item.textContent.toLowerCase();
        const matchBusqueda = texto.includes(input);
        const matchFiltro = filtroActual === 'todos' || item.dataset.categoria === filtroActual;
        item.style.display = (matchBusqueda && matchFiltro) ? 'block' : 'none';
    });
}

function filtrar(categoria) {
    filtroActual = categoria;
    
    // Actualizar botones
    document.querySelectorAll('.filtro-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Aplicar filtro
    const items = document.querySelectorAll('.registro-item');
    items.forEach(item => {
        if (categoria === 'todos') {
            item.style.display = 'block';
        } else {
            item.style.display = item.dataset.categoria === categoria ? 'block' : 'none';
        }
    });
}

// ==================== ACTUALIZACIÓN DE UI ====================
function actualizarLista() {
    const lista = document.getElementById('listaGastos');
    
    if (gastos.length === 0) {
        lista.innerHTML = '<p class="empty-message">No hay gastos registrados</p>';
        return;
    }
    
    lista.innerHTML = gastos.map(gasto => `
        <div class="registro-item" data-id="${gasto.id}" data-categoria="${gasto.categoria}">
            <div class="registro-header">
                <span class="registro-titulo">${gasto.descripcion}</span>
                <div class="registro-acciones">
                    <span class="badge badge-categoria ${gasto.categoria}">${capitalizar(gasto.categoria)}</span>
                    <span class="registro-fecha">${formatearFecha(gasto.fecha)}</span>
                    <button class="btn-eliminar" onclick="eliminarRegistro(${gasto.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="registro-detalles">
                <span class="registro-monto gasto">
                    <i class="fas fa-minus-circle"></i> ${formatearMoneda(gasto.monto)}
                </span>
            </div>
        </div>
    `).join('');
}

function actualizarResumen() {
    const hoy = new Date().toISOString().split('T')[0];
    const gastosHoy = gastos.filter(g => g.fecha === hoy);
    const totalHoy = gastosHoy.reduce((sum, g) => sum + g.monto, 0);
    const totalGeneral = gastos.reduce((sum, g) => sum + g.monto, 0);
    
    document.getElementById('totalGastos').textContent = formatearMoneda(totalGeneral);
    document.getElementById('gastosHoy').textContent = formatearMoneda(totalHoy);
    document.getElementById('cantidadGastos').textContent = gastos.length;
}

// ==================== ALMACENAMIENTO ====================
function guardarDatos() {
    localStorage.setItem('inventario_gastos', JSON.stringify(gastos));
}

function cargarDatos() {
    const datos = localStorage.getItem('inventario_gastos');
    if (datos) {
        gastos = JSON.parse(datos);
    }
}

// ==================== FUNCIONES AUXILIARES ====================
function capitalizar(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatearMoneda(valor) {
    return '$' + valor.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function formatearFecha(fecha) {
    const opciones = { day: '2-digit', month: 'short', year: 'numeric' };
    return new Date(fecha + 'T00:00:00').toLocaleDateString('es-ES', opciones);
}

function limpiarFormulario() {
    document.getElementById('formGastos').reset();
    document.getElementById('gastoFecha').value = new Date().toISOString().split('T')[0];
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
