"""
Middleware para capturar información de la request (usuario, IP) 
y hacerla disponible para los signals de auditoría.
"""
import threading

# Almacenamiento local de thread para la request actual
_thread_locals = threading.local()


def get_current_request():
    """Obtiene la request actual del thread local."""
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    """Obtiene el usuario actual de la request."""
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user
    return None


class AuditoriaMiddleware:
    """
    Middleware que guarda la request actual en thread local
    para que los signals de auditoría puedan acceder a ella.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Guardar request en thread local
        _thread_locals.request = request
        
        # Procesar la request
        response = self.get_response(request)
        
        # Limpiar
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        
        return response
