from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.groups.filter(name__in=allowed_roles).exists() or user.is_superuser:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("No tienes permiso para acceder a esta vista.")
        return _wrapped_view
    return decorator
