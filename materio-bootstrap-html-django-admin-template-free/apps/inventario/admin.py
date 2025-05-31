from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ( 'nombre',)
    search_fields = ( 'nombre',)

@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'longitud', 'latitud')
    search_fields = ('nombre', 'longitud', 'latitud')

@admin.register(ProductosVendido)
class ProductosVendidoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad', 'tienda', 'fecha_venta')
    search_fields = ('nombre', 'cantidad', 'tienda', 'fecha_venta')

@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cp')
    search_fields = ('nombre', 'cp')

@admin.register(ExistenciasBodegas)
class ExistenciasBodegasAdmin(admin.ModelAdmin):
    list_display = ('producto', 'bodega')

@admin.register(ExistenciasTienda)
class ExistenciasTiendaAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tienda')

@admin.register(Iteracion)
class IteracionAdmin(admin.ModelAdmin):
    list_display = ('numero_iteracion', 'producto')
    list_filter = ('numero_iteracion',)
    search_fields = ('producto__nombre',)
    ordering = ('-numero_iteracion',)
    
@admin.register(TransferenciaHistorial)
class TransferenciaHistorialAdmin(admin.ModelAdmin):
    list_display = ('producto', 'iteracion')
    list_filter = ('iteracion',)
    search_fields = ('producto__nombre',)
