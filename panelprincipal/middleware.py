from django.shortcuts import redirect
from django.urls import reverse


class SuscripcionMiddleware:
    """
    Middleware que verifica si el usuario tiene una suscripción activa.
    Si la suscripción está vencida o suspendida, redirige a la página de cuenta suspendida.
    """
    
    URLS_EXCLUIDAS = [
        '/login/',
        '/logout/',
        '/cuenta-suspendida/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # No verificar para URLs excluidas
        for url in self.URLS_EXCLUIDAS:
            if request.path.startswith(url):
                return self.get_response(request)
        
        # No verificar para archivos estáticos
        if request.path.startswith('/static/'):
            return self.get_response(request)
        
        # Si no está autenticado, el LoginRequiredMiddleware se encarga
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Los superusuarios siempre tienen acceso
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Verificar suscripción
        if hasattr(request.user, 'suscripcion'):
            if not request.user.suscripcion.esta_activa:
                return redirect('cuenta_suspendida')
        
        return self.get_response(request)
