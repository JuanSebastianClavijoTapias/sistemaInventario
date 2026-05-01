#!/usr/bin/env python3
import json

# Leer archivo actual
with open('registros.json', 'r', encoding='utf-8') as f:
    datos = json.load(f)

# Modelos de sistema que Django regenera automáticamente
MODELOS_SISTEMA = [
    'auth.permission',
    'auth.group', 
    'auth.user',
    'contenttypes.contenttype',
    'admin.logentry',
    'sessions.session',
]

# Modelos de negocio que queremos mantener
MODELOS_NEGOCIO = [
    'panelprincipal.configuracionsemana',
    'panelprincipal.liquidacionsemanal',
    'panelprincipal.suscripcion',
    'clientes.clientes',
    'proveedores.proveedores',
    'productos.productos',
    'gastos.gastos',
    'ventas.venta',
    'ventas.cobro',
    'ventas.detalleventa',
]

# Filtrar solo datos de negocio
datos_limpios = [r for r in datos if r['model'] in MODELOS_NEGOCIO]

print(f"Registros originales: {len(datos)}")
print(f"Registros finales (solo negocio): {len(datos_limpios)}")

# Guardar
with open('registros.json', 'w', encoding='utf-8') as f:
    json.dump(datos_limpios, f, ensure_ascii=False, indent=2)

print("✓ Archivo limpio generado")
