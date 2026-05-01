#!/usr/bin/env python3
"""
Script para limpiar datos duplicados en registros.json
- Consolida 3 proveedores "rh" en uno
- Elimina sesiones transitorias
- Elimina productos sin referencias
"""

import json
import sys

def limpiar_registros(archivo_json):
    # Cargar datos
    with open(archivo_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    print(f"Registros iniciales: {len(datos)}")
    
    # Mapeo de cambios: proveedor_viejo -> proveedor_nuevo
    proveedor_map = {
        18: 19,  # Consolidar pk 18 al 19
        20: 19,  # Consolidar pk 20 al 19
    }
    
    # Recolectar productos que usan el proveedor 18 (será eliminado)
    productos_eliminar = set()
    for registro in datos:
        if registro.get('model') == 'productos.productos' and registro['fields'].get('proveedor') == 18:
            productos_eliminar.add(registro['pk'])
    
    print(f"\nProveedores duplicados encontrados: 3 registros de 'rh' (pk 18, 19, 20)")
    print(f"Consolidando en: proveedor pk 19")
    print(f"Productos a eliminar (sin proveedor): {productos_eliminar}")
    
    # Nuevos datos limpios
    datos_limpios = []
    
    for registro in datos:
        skip = False
        
        # Eliminar sesiones transitorias
        if registro.get('model') == 'sessions.session':
            skip = True
            print(f"Eliminando sesión: {registro['pk']}")
        
        # Eliminar proveedores duplicados (18 y 20)
        elif registro.get('model') == 'proveedores.proveedores' and registro['pk'] in [18, 20]:
            skip = True
            print(f"Eliminando proveedor duplicado pk {registro['pk']}")
        
        # Eliminar productos sin proveedor valido
        elif registro.get('model') == 'productos.productos' and registro['pk'] in productos_eliminar:
            skip = True
            print(f"Eliminando producto pk {registro['pk']} (proveedor eliminado)")
        
        # Actualizar referencias de proveedor
        elif registro.get('model') in ['productos.productos', 'gastos.gastos']:
            proveedor_viejo = registro['fields'].get('proveedor')
            if proveedor_viejo in proveedor_map:
                registro['fields']['proveedor'] = proveedor_map[proveedor_viejo]
                print(f"Actualizando {registro['model']} pk {registro['pk']}: proveedor {proveedor_viejo} -> {proveedor_map[proveedor_viejo]}")
        
        if not skip:
            datos_limpios.append(registro)
    
    print(f"\nRegistros finales: {len(datos_limpios)}")
    print(f"Registros eliminados: {len(datos) - len(datos_limpios)}")
    
    # Guardar archivo limpio
    with open(archivo_json, 'w', encoding='utf-8') as f:
        json.dump(datos_limpios, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Archivo limpio guardado: {archivo_json}")

if __name__ == '__main__':
    archivo = '/home/samuel/Descargas/gamora_papa/sistemaInventario/registros.json'
    limpiar_registros(archivo)
