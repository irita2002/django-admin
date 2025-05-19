from django.urls import path
from .views import inventario
from .views import existencias_combinadas
from . import views
urlpatterns = [
    path(
        "listar",
        inventario.as_view(template_name="inventario.html"),
        name="inventario",
        
    ),
    path('existencias-totales/', existencias_combinadas, name='existencias_combinadas'),
    path('transferencias/', views.transferir_producto, name='transferir_producto'),
    path('bodegas/<int:bodega_id>/', views.detalle_bodega_iteracion, name='detalle_bodega'),
    path('iteraciones-producto/', views.iteraciones_por_producto, name='iteraciones_producto'),
    path('', views.mapa_principal, name='mapa_principal'),
    
]
