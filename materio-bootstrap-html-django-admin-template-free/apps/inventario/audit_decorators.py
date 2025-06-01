from functools import wraps
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
import json
from .models import AuditoriaAcciones

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def auditar_accion(accion, modelo=None, descripcion_personalizada=None):
    """
    Decorador para auditar acciones de usuarios
    
    Args:
        accion: Tipo de acción (CREATE, UPDATE, DELETE, VIEW, etc.)
        modelo: Nombre del modelo (se puede inferir automáticamente)
        descripcion_personalizada: Descripción personalizada de la acción
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Ejecutar la función original
            response = func(request, *args, **kwargs)
            
            try:
                # Determinar el modelo si no se especifica
                if not modelo:
                    # Intentar inferir del nombre de la función
                    func_name = func.__name__
                    if 'producto' in func_name.lower():
                        modelo_inferido = 'Producto'
                    elif 'tienda' in func_name.lower():
                        modelo_inferido = 'Tienda'
                    elif 'bodega' in func_name.lower():
                        modelo_inferido = 'Bodega'
                    elif 'existencia' in func_name.lower():
                        modelo_inferido = 'Existencias'
                    elif 'transfer' in func_name.lower():
                        modelo_inferido = 'Transferencia'
                    else:
                        modelo_inferido = 'Sistema'
                else:
                    modelo_inferido = modelo
                
                # Obtener información del objeto si está en kwargs o args
                objeto_id = kwargs.get('pk') or kwargs.get('id') or kwargs.get('producto_id') or kwargs.get('tienda_id') or kwargs.get('bodega_id')
                
                # Generar descripción
                if descripcion_personalizada:
                    descripcion = descripcion_personalizada
                else:
                    descripcion = f"{accion.lower().capitalize()} en {func_name}"
                
                # Obtener datos adicionales del request
                datos_adicionales = {}
                if request.method == 'POST':
                    # Solo capturar campos relevantes, no contraseñas
                    post_data = dict(request.POST)
                    # Remover campos sensibles
                    campos_sensibles = ['password', 'csrfmiddlewaretoken', 'confirm_password']
                    for campo in campos_sensibles:
                        post_data.pop(campo, None)
                    datos_adicionales['post_data'] = post_data
                
                if request.GET:
                    datos_adicionales['get_params'] = dict(request.GET)
                
                # Crear registro de auditoría
                AuditoriaAcciones.objects.create(
                    usuario=request.user if not isinstance(request.user, AnonymousUser) else None,
                    accion=accion,
                    modelo=modelo_inferido,
                    objeto_id=str(objeto_id) if objeto_id else None,
                    descripcion=descripcion,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    datos_adicionales=datos_adicionales if datos_adicionales else None
                )
                
            except Exception as e:
                # No queremos que la auditoría rompa la funcionalidad principal
                print(f"Error en auditoría: {e}")
            
            return response
        return wrapper
    return decorator
def registrar_auditoria_manual(request, accion, modelo, objeto_id=None, objeto_nombre=None, descripcion="", datos_adicionales=None):
    """
    Función para registrar auditorías de forma manual cuando no se puede usar el decorador
    """
    try:
        AuditoriaAcciones.objects.create(
            usuario=request.user if not isinstance(request.user, AnonymousUser) else None,
            accion=accion,
            modelo=modelo,
            objeto_id=str(objeto_id) if objeto_id else None,
            objeto_nombre=objeto_nombre,
            descripcion=descripcion,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            datos_adicionales=datos_adicionales
        )
    except Exception as e:
        print(f"Error en auditoría manual: {e}")