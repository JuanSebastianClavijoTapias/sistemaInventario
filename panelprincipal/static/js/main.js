// ==================== DATOS ====================
// Cargar datos de localStorage al iniciar
document.addEventListener('DOMContentLoaded', function() {
    actualizarResumenPrincipal();
});

// ==================== FUNCIONES DE RESUMEN ====================
function actualizarResumenPrincipal() {
    // Cargar datos de cada sección
    const ventas = JSON.parse(localStorage.getItem('inventario_ventas') || '[]');
    const clientes = JSON.parse(localStorage.getItem('inventario_clientes') || '[]');
    const proveedores = JSON.parse(localStorage.getItem('inventario_proveedores') || '[]');
    const gastos = JSON.parse(localStorage.getItem('inventario_gastos') || '[]');
    
    // Calcular ingresos (ventas + pagos de clientes)
    const ingresoVentas = ventas.reduce((sum, v) => sum + (v.total || 0), 0);
    const ingresoClientes = clientes.reduce((sum, c) => sum + (c.inicial || 0), 0);
    const totalIngresos = ingresoVentas + ingresoClientes;
    
    // Calcular gastos (gastos registrados + pagos a proveedores)
    const gastosRegistrados = gastos.reduce((sum, g) => sum + (g.monto || 0), 0);
    const pagosProveedores = proveedores.reduce((sum, p) => sum + (p.inicial || 0), 0);
    const totalGastos = gastosRegistrados + pagosProveedores;
    
    // Calcular balance
    const balance = totalIngresos - totalGastos;
    
    // Calcular deudas
    const totalPorCobrar = clientes.reduce((sum, c) => sum + (c.saldo || 0), 0);
    const totalPorPagar = proveedores.reduce((sum, p) => sum + (p.saldo || 0), 0);
    
    // Contar registros
    const hoy = new Date().toISOString().split('T')[0];
    const ventasHoy = ventas.filter(v => v.fecha === hoy).length;
    
    // Actualizar UI
    document.getElementById('totalIngresos').textContent = formatearMoneda(totalIngresos);
    document.getElementById('totalGastos').textContent = formatearMoneda(totalGastos);
    document.getElementById('totalFinanzas').textContent = formatearMoneda(balance);
    document.getElementById('totalPorCobrar').textContent = formatearMoneda(totalPorCobrar);
    document.getElementById('totalPorPagar').textContent = formatearMoneda(totalPorPagar);
    
    // Actualizar contadores
    document.getElementById('countVentas').textContent = `${ventasHoy} hoy`;
    document.getElementById('countClientes').textContent = `${clientes.length} registros`;
    document.getElementById('countProveedores').textContent = `${proveedores.length} activos`;
    document.getElementById('countGastos').textContent = formatearMoneda(gastosRegistrados);
}

// ==================== FUNCIONES AUXILIARES ====================
function formatearMoneda(valor) {
    return '$' + valor.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}