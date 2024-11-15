from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ( 'cantidad',)
    search_fields = ( 'cantidad',)

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