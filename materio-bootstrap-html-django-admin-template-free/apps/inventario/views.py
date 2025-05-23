from django.shortcuts import render, redirect
from .models import Producto,ExistenciasBodegas, ExistenciasTienda,Bodega,Tienda
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.db.models import Sum
from django.contrib import messages
from .forms import TransferenciaForm
from django.db import transaction
from web_project.template_helpers.theme import TemplateHelper
from .utils.map_generator import generar_mapa_offline

class inventario(TemplateView):
    template_name = 'inventario.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
    
        # Acceso a datos del modelo
        mis_productos = Producto.objects.all()
        context['productos'] = mis_productos
        context.update(
            {
                "is_menu": False,
            }
        )

        TemplateHelper.map_context(context)
        return context



class detalles(TemplateView):
    template_name = 'detalles.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
    
        # Acceso a datos del modelo
        mis_productos = Producto.objects.all()
        context['productos'] = mis_productos

        return context


def existencias_combinadas(request):
    productos = Producto.objects.all()
    producto_seleccionado = None
    existencias_bodegas = []
    existencias_tiendas = []
    total_bodegas = 0
    total_tiendas = 0
    gran_total = 0

    if 'producto_id' in request.GET:
        producto_id = request.GET['producto_id']
        producto_seleccionado = Producto.objects.get(id=producto_id)
        
        # Existencias en BODEGAS
        existencias_bodegas = ExistenciasBodegas.objects.filter(
            producto=producto_seleccionado
        ).select_related('bodega')
        
        total_bodegas = existencias_bodegas.aggregate(
            total=Sum('cantidad')
        )['total'] or 0

        # Existencias en TIENDAS
        existencias_tiendas = ExistenciasTienda.objects.filter(
            producto=producto_seleccionado
        ).select_related('tienda')
        
        total_tiendas = existencias_tiendas.aggregate(
            total=Sum('cantidad')
        )['total'] or 0

        # Total general
        gran_total = total_bodegas + total_tiendas

    return render(request, 'existencias_combinadas.html', {
        'productos': productos,
        'producto_seleccionado': producto_seleccionado,
        'existencias_bodegas': existencias_bodegas,
        'existencias_tiendas': existencias_tiendas,
        'total_bodegas': total_bodegas,
        'total_tiendas': total_tiendas,
        'gran_total': gran_total,
        'layout_path': TemplateHelper.set_layout("layout_blank.html"),
    })



from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ExistenciasTienda, ExistenciasBodegas, TransferenciaHistorial, Iteracion
from .forms import TransferenciaForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
@login_required
def transferir_producto(request):
    if request.method == 'POST':
        form = TransferenciaForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            tienda = form.cleaned_data['tienda']
            bodega = form.cleaned_data['bodega']
            cantidad = form.cleaned_data['cantidad']
            numero_iteracion = form.cleaned_data['numero_iteracion']
            fecha_transferencia = form.cleaned_data['fecha_transferencia']

            try:
                existencia_tienda = ExistenciasTienda.objects.get(
                    producto=producto,
                    tienda=tienda
                )
                
                if existencia_tienda.cantidad < cantidad:
                    messages.error(request, 'Cantidad insuficiente en la tienda')
                    return redirect('transferir_producto')

                with transaction.atomic():
                    # Actualizar existencias
                    existencia_tienda.cantidad -= cantidad
                    existencia_tienda.save()

                    existencia_bodega, created = ExistenciasBodegas.objects.get_or_create(
                        producto=producto,
                        bodega=bodega,
                        defaults={'cantidad': cantidad}
                    )
                    if not created:
                        existencia_bodega.cantidad += cantidad
                        existencia_bodega.save()

                    # Crear o actualizar iteración
                    iteracion, created = Iteracion.objects.get_or_create(
                        numero_iteracion=numero_iteracion,
                        producto=producto,
                    )
                    

                    # Registrar en el historial
                    TransferenciaHistorial.objects.create(
                        producto=producto,
                        bodega=bodega,
                        cantidad=cantidad,
                        iteracion=iteracion,
                        fecha_transferencia=fecha_transferencia
                    )

                messages.success(request, f'Transferencia a {bodega.nombre} registrada en Iteración {numero_iteracion}')
                return redirect('transferir_producto')

            except ExistenciasTienda.DoesNotExist:
                messages.error(request, 'El producto no existe en esta tienda')
                return redirect('transferir_producto')

    else:
        form = TransferenciaForm()

    return render(request, 'transferencia.html', {'form': form,'layout_path': TemplateHelper.set_layout("layout_blank.html"),})

from django.shortcuts import render
from .models import Producto, Iteracion
from django.template.defaulttags import register
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, False)

def iteraciones_por_producto(request):
    producto_seleccionado = None
    iteracion_seleccionado = None
    iteracion_id=0
    iteraciones={}
    iteraciones_agrupadas = {}
    iteraciones_t = None
    bodegas = Bodega.objects.all()
    if 'producto_id' in request.GET:
        producto_id = request.GET['producto_id']
        producto_seleccionado = Producto.objects.get(id=producto_id)
        print(producto_seleccionado)
        if 'iteracion_id' in request.GET:
            iteracion_id = request.GET['iteracion_id']
        # Obtener todas las iteraciones del producto ordenadas
            iteraciones = Iteracion.objects.filter(
                producto=producto_seleccionado,
            )
        # Agrupar por número de iteración
        for iteracion in iteraciones:   
            num_iteracion = iteracion.numero_iteracion
            if num_iteracion not in iteraciones_agrupadas:
                iteraciones_agrupadas[num_iteracion] = []
            iteraciones_agrupadas[num_iteracion].append(iteracion)

    productos = Producto.objects.all()
    transferencia = TransferenciaHistorial.objects.filter(producto=producto_seleccionado,iteracion=iteracion_id).order_by('fecha_transferencia')
    iteracion_t = Iteracion.objects.all


    return render(request, 'iteraciones_producto.html', {
        'productos': productos,
        'producto_seleccionado': producto_seleccionado,
        'iteraciones_agrupadas': iteraciones,
        'iteracion_t':iteracion_t,
        'bodegas': bodegas, 
        'transferencias':transferencia,
        'layout_path': TemplateHelper.set_layout("layout_blank.html"),
        
    })

def detalle_bodega_iteracion(request, bodega_id):
    bodega = Bodega.objects.get(id=bodega_id)
    iteraciones = TransferenciaHistorial.objects.filter(
        bodega=bodega
    ).select_related('iteracion').order_by('-iteracion__numero_iteracion')
    
    # Agrupar por iteración
    datos_agrupados = {}
    for transferencia in iteraciones:
        num_iteracion = transferencia.iteracion.numero_iteracion
        if num_iteracion not in datos_agrupados:
            datos_agrupados[num_iteracion] = []
        datos_agrupados[num_iteracion].append(transferencia)
    
    return render(request, 'detalle_bodega.html', {
        'bodega': bodega,
        'datos_agrupados': datos_agrupados,
        'layout_path': TemplateHelper.set_layout("layout_blank.html"),

    })

def mapa_principal(request):
    tiendas = Tienda.objects.all()
    bodegas = Bodega.objects.all()
    mapa_html = generar_mapa_offline(list(tiendas) + list(bodegas))
    return render(request, 'map.html', {'mapa': mapa_html})