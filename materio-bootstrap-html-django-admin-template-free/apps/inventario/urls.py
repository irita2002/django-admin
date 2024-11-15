from django.urls import path
from .views import inventario


urlpatterns = [
    path(
        "listar",
        inventario.as_view(template_name="inventario.html"),
        name="inventario",
    )
]
