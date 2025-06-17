# apps/common/templatetags/permissions.py

from django import template
from django.core.exceptions import PermissionDenied
register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

def usuario_es_admin(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        # Definir grupo de administradores:
        if user.is_superuser or user.groups.filter(name="Coordinador").exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view
