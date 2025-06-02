from django.urls import path
from .views import existencias_combinadas, formulario_informe_ventas, informe_ventas_pdf, informe_ventas_pdf_form
from . import views
app_name = "inventario"
urlpatterns = [
    
    path('existencias-totales/', existencias_combinadas, name='existencias_combinadas'),
    path('transferencias/', views.transferir_producto, name='transferir_producto'),
    path('bodegas/<int:bodega_id>/', views.detalle_bodega_iteracion, name='detalle_bodega'),
    path('iteraciones-producto/', views.iteraciones_por_producto, name='iteraciones_producto'),
    path('', views.mapa_principal, name='mapa_principal'),
    path("productos/", views.ProductoListView.as_view(), name="list"),
    path("nuevo/", views.ProductoCreateView.as_view(), name="create"),
    path("productos/<int:pk>/", views.ProductoDetailView.as_view(), name="detail"),
    path("productos/<int:pk>/editar/", views.ProductoUpdateView.as_view(), name="update"),
    path("productos/<int:pk>/eliminar/", views.ProductoDeleteView.as_view(), name="delete"),
        # CRUD Tienda
    path("tiendas/",  views.TiendaListView.as_view(),  name="tienda_list"),
    path("tiendas/nueva/", views.TiendaCreateView.as_view(), name="tienda_create"),
    path("tiendas/<int:pk>/", views.TiendaDetailView.as_view(), name="tienda_detail"),
    path("tiendas/<int:pk>/editar/", views.TiendaUpdateView.as_view(), name="tienda_update"),
    path("tiendas/<int:pk>/eliminar/", views.TiendaDeleteView.as_view(), name="tienda_delete"),
    # URLs para gestión de existencias en tiendas
    path('tiendas/existencias/', views.agregar_existencias_tienda, name='agregar_existencias_tienda'),
    path('tiendas/existencias/<int:tienda_id>/', views.agregar_existencias_tienda, name='agregar_existencias_tienda_id'),
    path('tiendas/<int:tienda_id>/existencias/', views.listar_existencias_tienda, name='listar_existencias_tienda'),
    path('existencias/actualizar/<int:existencia_id>/', views.actualizar_existencia_tienda, name='actualizar_existencia_tienda'),
    
    # URLs AJAX
    path('ajax/tienda/<int:tienda_id>/existencias/', views.obtener_existencias_tienda_ajax, name='obtener_existencias_tienda_ajax'),
    path('ajax/actualizar-existencia/', views.actualizar_existencia_ajax, name='actualizar_existencia_ajax'),
    
    # CRUD Bodega
    path("bodegas/",views.BodegaListView.as_view(),name="bodega_list"),
    path("bodegas/nueva/",views.BodegaCreateView.as_view(),name="bodega_create"),
    path("bodegas/<int:pk>/",views.BodegaDetailView.as_view(),name="bodega_detail"),
    path("bodegas/<int:pk>/editar/",views.BodegaUpdateView.as_view(),name="bodega_update"),
    path("bodegas/<int:pk>/eliminar/",views.BodegaDeleteView.as_view(),name="bodega_delete"),
    # CRUD Circunscripción
    path("circunscripciones/",views.CircunscripcionListView.as_view(),name="circunscripcion_list"),
    path("circunscripciones/nueva/",views.CircunscripcionCreateView.as_view(),name="circunscripcion_create"),
    path("circunscripciones/<int:pk>/",views.CircunscripcionDetailView.as_view(),name="circunscripcion_detail"),
    path("circunscripciones/<int:pk>/editar/",views.CircunscripcionUpdateView.as_view(),name="circunscripcion_update"),
    path("circunscripciones/<int:pk>/eliminar/",views.CircunscripcionDeleteView.as_view(),name="circunscripcion_delete"),
    path('mapa/tiendas/', views.ver_tiendas, name='ver_tiendas'),
    # ruta para recargar mapa con tienda seleccionada
    path('mapa/tiendas/<int:tienda_id>/', views.ver_tiendas, name='ver_tiendas'),
    path('informe-formulario/', formulario_informe_ventas, name='formulario_informe'),
    path('informe-generar/', informe_ventas_pdf_form, name='informe_ventas_pdf_form'),
    path('informe-ventas/<int:producto_id>/<str:fecha_str>/', informe_ventas_pdf, name='informe_ventas_pdf'),
]
