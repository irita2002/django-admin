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
# @login_required
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
                    return redirect('inventario:transferir_producto')

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
                return redirect('inventario:transferir_producto')

            except ExistenciasTienda.DoesNotExist:
                messages.error(request, 'El producto no existe en esta tienda')
                return redirect('inventario:transferir_producto')

    else:
        form = TransferenciaForm()

    return render(request, 'transferencia.html', {'form': form,'layout_path': TemplateHelper.set_layout("layout_blank.html"),})

from django.shortcuts import render
from .models import Producto, Iteracion
from django.template.defaulttags import register
# @register.filter
def get_item(dictionary, key):
    return dictionary.get(key, False)

def iteraciones_por_producto(request):
    producto_seleccionado = None
    iteracion_id=0
    iteraciones={}
    iteraciones_agrupadas = {}
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
    try:
        transferencia = TransferenciaHistorial.objects.filter(producto=producto_seleccionado,iteracion=iteraciones[0].id).order_by('fecha_transferencia')
    except:
        transferencia=TransferenciaHistorial.objects.filter(producto=producto_seleccionado,iteracion=iteracion_id).order_by('fecha_transferencia')
    iteracion_t = Iteracion.objects.all

    return render(request, 'iteraciones_producto.html', {
        'productos': productos,
        'producto_seleccionado': producto_seleccionado,
        'iteraciones_agrupadas': iteraciones_agrupadas,
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
    productos = Producto.objects.all()
    mapa_html = generar_mapa_offline(list(tiendas) + list(bodegas))
    return render(request, 'map.html', {'mapa': mapa_html,'tiendas': tiendas,'bodegas': bodegas,'productos':productos})
#///////////////////Producto////////////////////////
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Producto

class ProductoListView(ListView):
    model = Producto
    template_name = "producto/producto_list.html"
    context_object_name = "productos"

    def get_queryset(self):
        return (
            Producto.objects
            .annotate(
                cantidad_tiendas=Sum('existenciastienda__cantidad'),
                cantidad_bodegas=Sum('existenciasbodegas__cantidad'),
                total=Sum('existenciastienda__cantidad')+Sum('existenciasbodegas__cantidad'),
            )
            .order_by('nombre')
        )

class ProductoDetailView(DetailView):
    model = Producto
    template_name = "producto/producto_detail.html"
    context_object_name = "producto"

# apps/inventario/views.py

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from .models import Producto

# ———————————————————————————————
# 1) Listado de Productos
# ———————————————————————————————


# ———————————————————————————————
# 2) Crear Producto (AJAX)
# ———————————————————————————————
class ProductoCreateView(CreateView):
    model = Producto
    fields = ["nombre"  ]  # Ajusta según tus campos reales
    template_name = "producto/producto_form.html"
    success_url = reverse_lazy("inventario:list")

    def form_invalid(self, form):
        # Si viene AJAX y no es válido, devolvemos solo el fragmento con errores
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            context = self.get_context_data(form=form, object=None)
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    def form_valid(self, form):
        # Si viene AJAX y es válido, devolvemos { success: True }
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def get(self, request, *args, **kwargs):
        # Si es AJAX, enviamos solo el fragmento de formulario (vacío)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = None
            form = self.get_form()
            context = self.get_context_data(form=form, object=None)
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({"success": True, "html": html})
        # Si no es AJAX, comportamiento normal
        return super().get(request, *args, **kwargs)


# ———————————————————————————————
# 3) Editar Producto (AJAX)
# ———————————————————————————————
class ProductoUpdateView(UpdateView):
    model = Producto
    fields = ["nombre"]  # Mismos campos que en CreateView
    template_name = "producto/producto_form.html"
    success_url = reverse_lazy("inventario:list")

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            context = self.get_context_data(form=form, object=self.get_object())
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = self.get_object()
            form = self.get_form()
            context = self.get_context_data(form=form, object=self.object)
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({"success": True, "html": html})
        return super().get(request, *args, **kwargs)


# ———————————————————————————————
# 4) Eliminar Producto (AJAX)
# ———————————————————————————————
class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = "producto/producto_confirm_delete.html"
    success_url = reverse_lazy("inventario:producto_list")

    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            html = render_to_string(
                "producto/producto_delete_modal.html",
                {"object": self.object},
                request=request
            )
            return JsonResponse({"success": True, "html": html})
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Aquí hacemos la lógica de borrado en POST y devolvemos JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            self.object.delete()
            return JsonResponse({"success": True})
        return super().post(request, *args, **kwargs)


#///////////////////Tiendas////////////////////////
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from .models import Tienda
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from .models import Tienda



class TiendaDetailView(DetailView):
    model = Tienda
    template_name = "tienda/tienda_detail.html"
    context_object_name = "tienda"

class TiendaListView(ListView):
    model = Tienda
    template_name = "tienda/tienda_list.html"
    context_object_name = "tiendas"


class TiendaCreateView(CreateView):
    model = Tienda
    fields = ["nombre", "latitud", "longitud", "tipo"]
    template_name = "tienda/tienda_form.html"
    success_url = reverse_lazy("inventario:tienda_list")

    def form_invalid(self, form):
        # Si es petición AJAX, devolvemos solo el HTML del formulario (con errores)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            context = self.get_context_data(form=form, object=None)
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    def form_valid(self, form):
        # Guardamos la nueva Tienda
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            # En AJAX devolvemos solo success=True (sin recargar la página completa)
            return JsonResponse({"success": True})
        return response

    def get(self, request, *args, **kwargs):
        # Si la petición es AJAX, devolvemos solo el fragmento del formulario
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = None
            form = self.get_form()
            context = self.get_context_data(form=form, object=None)
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({"success": True, "html": html})
        # Si no es AJAX, comportarse como siempre y renderizar todo el template
        return super().get(request, *args, **kwargs)


class TiendaUpdateView(UpdateView):
    model = Tienda
    fields = ["nombre", "latitud", "longitud", "tipo"]
    template_name = "tienda/tienda_form.html"
    success_url = reverse_lazy("inventario:tienda_list")

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            # Renderizamos solo el HTML del formulario con errores
            context = self.get_context_data(form=form, object=self.get_object())
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = self.get_object()
            form = self.get_form()
            context = self.get_context_data(form=form, object=self.object)
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({"success": True, "html": html})
        return super().get(request, *args, **kwargs)


from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from .models import Tienda

class TiendaDeleteView(DeleteView):
    model = Tienda
    template_name = "tienda/tienda_confirm_delete.html"  # Vista completa para peticiones no-AJAX
    success_url = reverse_lazy("inventario:tienda_list")

    def get(self, request, *args, **kwargs):
        """
        Si es petición AJAX (por ejemplo, al hacer clic en “Eliminar” desde la lista),
        devolvemos únicamente el formulario (partial) para inyectar en el modal.
        """
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            # Renderizamos únicamente el fragmento de confirmación:
            html = render_to_string(
                "tienda/tienda_delete_modal.html",
                {"object": self.object},
                request=request
            )
            return JsonResponse({"success": True, "html": html})
        # Si no es AJAX, se comporta como siempre:
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Aquí movemos la lógica de borrado:
        - Si viene por AJAX, borramos y devolvemos JSON {"success": True}.
        - Si viene como POST normal (por ejemplo un navegador sin JS), usamos el flujo del DeleteView.
        """
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            # Eliminamos la instancia:
            self.object.delete()
            return JsonResponse({"success": True})
        # Si no es AJAX, llamamos al DeleteView original (que internamente llama a delete() y redirige)
        return super().post(request, *args, **kwargs)

#///////////////////Bodegas////////////////////////
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from .models import Bodega

class BodegaListView(ListView):
    model = Bodega
    template_name = "bodega/bodega_list.html"
    context_object_name = "bodegas"

class BodegaDetailView(DetailView):
    model = Bodega
    template_name = "bodega/bodega_detail.html"
    context_object_name = "bodega"

class BodegaCreateView(CreateView):
    model = Bodega
    fields = ["nombre", "cp", "cantidad_nucleos", "latitud", "longitud", "orden"]
    template_name = "bodega/bodega_form.html"
    success_url = reverse_lazy("inventario:bodega_list")

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return response

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.get_form()
            html = render_to_string(self.template_name, {'form': form, 'object': None}, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)

class BodegaUpdateView(UpdateView):
    model = Bodega
    fields = ["nombre", "cp", "cantidad_nucleos", "latitud", "longitud", "orden"]
    template_name = "bodega/bodega_form.html"
    success_url = reverse_lazy("inventario:bodega_list")
    
    def form_invalid(self, form):
        # si es AJAX, devolvemos el formulario con errores
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def form_valid(self, form):
        # guardamos y devolvemos señal de éxito
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return response

    def get(self, request, *args, **kwargs):
        # si es AJAX, devolvemos sólo el HTML del formulario
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            form = self.get_form()
            html = render_to_string(self.template_name, {'form': form, 'object': self.object}, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)


# apps/inventario/views.py

from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from .models import Bodega

class BodegaDeleteView(DeleteView):
    model = Bodega
    template_name = "bodega/bodega_confirm_delete.html"  # Para peticiones normales
    success_url = reverse_lazy("inventario:bodega_list")

    def get(self, request, *args, **kwargs):
        """
        Si la petición es AJAX, devolvemos solo el fragmento de confirmación
        para inyectar en el modal (bodega_delete_modal.html).
        """
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            html = render_to_string(
                "bodega/bodega_delete_modal.html",
                {"object": self.object},
                request=request
            )
            return JsonResponse({"success": True, "html": html})
        # Si no es AJAX, se comporta como DeleteView normal:
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Si la petición es AJAX (submit desde el modal), borramos y devolvemos JSON.
        """
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            self.object.delete()
            return JsonResponse({"success": True})
        # Si no es AJAX, continuar con el flujo habitual:
        return super().post(request, *args, **kwargs)


#///////////////////Circunscripcion////////////////////////
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from .models import Circunscripcion


class CircunscripcionDetailView(DetailView):
    model = Circunscripcion
    template_name = "circunscripcion/circunscripcion_detail.html"
    context_object_name = "circunscripcion"

class CircunscripcionListView(ListView):
    model = Circunscripcion
    template_name = "circunscripcion/circunscripcion_list.html"
    context_object_name = "circunscripciones"

class CircunscripcionCreateView(CreateView):
    model = Circunscripcion
    fields = ["nombre", "ancianos", "ninos", "embarazadas"]
    template_name = "circunscripcion/circunscripcion_form.html"
    success_url = reverse_lazy("inventario:circunscripcion_list")

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return response

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = None
            form = self.get_form()
            context = self.get_context_data(form=form, object=self.object)
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)

class CircunscripcionUpdateView(UpdateView):
    model = Circunscripcion
    fields = ["nombre", "ancianos", "ninos", "embarazadas"]
    template_name = "circunscripcion/circunscripcion_form.html"
    success_url = reverse_lazy("inventario:circunscripcion_list")

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return response

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            form = self.get_form()
            context = self.get_context_data(form=form, object=self.object)
            html = render_to_string(self.template_name, context, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)

from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from .models import Circunscripcion

class CircunscripcionDeleteView(DeleteView):
    model = Circunscripcion
    template_name = "circunscripcion/circunscripcion_confirm_delete.html"  # Para peticiones normales
    success_url = reverse_lazy("inventario:circunscripcion_list")

    def get(self, request, *args, **kwargs):
        """
        Si la petición es AJAX, devolvemos solo el fragmento 'circunscripcion_delete_modal.html'.
        """
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            html = render_to_string(
                "circunscripcion/circunscripcion_delete_modal.html",
                {"object": self.object},
                request=request
            )
            return JsonResponse({"success": True, "html": html})
        # Si no es AJAX, usamos el flujo normal de DeleteView (muestra pagina completa)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Si la petición es AJAX (confirmación dentro del modal), borramos y devolvemos JSON.
        """
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                self.object = self.get_object()
            except Http404:
                return JsonResponse({"success": False}, status=404)
            self.object.delete()
            return JsonResponse({"success": True})
        # Si no es AJAX, delegamos al DeleteView normal
        return super().post(request, *args, **kwargs)

##################################Mapa##################################################
# tuapp/views.py
import osmnx as ox
import networkx as nx
from shapely.geometry import Point
from django.db.models import Sum

def recomendar_bodega(tienda_origen, producto, alfa=0.7, beta=0.3):
    # 1. Obtener ubicación de tienda
    tienda = Tienda.objects.get(id=tienda_origen)

    
    lat0 = float(tienda.latitud)
    lon0 = float(tienda.longitud)
    print(str(lat0)+"+"+ str(lon0))
    # 2. Descargar grafo vial y proyectar
    G = ox.graph_from_point((lat0, lon0), dist=3000, network_type='drive')
    G_proj = ox.project_graph(G)

    geom0, _ = ox.projection.project_geometry(Point(lon0, lat0), to_crs=G_proj.graph['crs'])
    nodo_origen = ox.distance.nearest_nodes(G_proj, geom0.x, geom0.y)

    # 3. Calcular necesidad y distancia por bodega
    from apps.inventario.models import Bodega, TransferenciaHistorial
    bodegas = Bodega.objects.all()

    resultados = []

    max_necesidad = 0
    max_distancia = 1  # evitar división por cero

    for bodega in bodegas:
        lat_b = bodega.latitud
        lon_b = bodega.longitud

        geom_b, _ = ox.projection.project_geometry(Point(lon_b, lat_b), to_crs=G_proj.graph['crs'])
        nodo_b = ox.distance.nearest_nodes(G_proj, geom_b.x, geom_b.y)

        distancia = nx.shortest_path_length(G_proj, nodo_origen, nodo_b, weight='length')  # en metros

        entregado = TransferenciaHistorial.objects.filter(
            producto=producto,
            bodega=bodega
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        necesidad = max(bodega.cantidad_nucleos - entregado, 0)

        max_necesidad = max(max_necesidad, necesidad)
        max_distancia = max(max_distancia, distancia)

        resultados.append({
            'bodega': bodega,
            'necesidad': necesidad,
            'distancia': distancia,
            'latitud':lat_b,
            'longitud':lon_b
        })

    # 4. Normalizar y calcular score
    recomendaciones = []
    for r in resultados:
        necesidad_n = r['necesidad'] / max_necesidad if max_necesidad else 0
        distancia_n = r['distancia'] / max_distancia if max_distancia else 0
        score = alfa * necesidad_n - beta * distancia_n

        recomendaciones.append({
            'bodega': r['bodega'],
            'necesidad': r['necesidad'],
            'distancia_m': round(r['distancia']),
            'score': round(score, 4),
            'latitud':r['latitud'],
            'longitud':r['longitud'],
        })

    recomendaciones = sorted(recomendaciones, key=lambda x: x['score'], reverse=True)
    return recomendaciones

from django.shortcuts import render, get_object_or_404
from .models import Tienda
from .utils.map_generator import generar_mapa_offline

def ver_tiendas(request, tienda_id=None):
    bodegas = Bodega.objects.all()
    mapa_html = None
    producto_seleccionado = None
    tiendas = Tienda.objects.all()
    productos = Producto.objects.all()
    recomendaciones = []  # Inicializar como lista vacía
    
    if tienda_id:
        # si hay una tienda seleccionada, úsala como origen
        tienda_origen = get_object_or_404(Tienda, pk=tienda_id)
        # pasamos **solo** esa tienda (o bien la lista completa si quieres mostrar distancias al resto)
        mapa_html = generar_mapa_offline(
            ubicaciones=bodegas,
            direccion_origen=f"{tienda_origen.latitud},{tienda_origen.longitud}"
        )
        
        # Solo obtener recomendaciones si hay tienda seleccionada
        if 'producto_id' in request.GET:
            producto_id = request.GET['producto_id']
            producto_seleccionado = Producto.objects.get(id=producto_id)
            print(producto_seleccionado)
        
        # AQUÍ ESTÁ LA CORRECCIÓN: Solo llamar recomendar_bodega si hay tienda
        recomendaciones = recomendar_bodega(tienda_id, producto_seleccionado)
        
    else:
        # sin tienda seleccionada, mapa centrado en coordenadas por defecto
        mapa_html = generar_mapa_offline(ubicaciones=bodegas)
        # NO llamamos recomendar_bodega cuando no hay tienda seleccionada

    
    return render(request, 'map.html', {
        'Bodega': bodegas,
        'tiendas': tiendas,
        'mapa': mapa_html,
        'tienda_seleccionada': tienda_id,
        'producto_seleccionado': producto_seleccionado,
        'recomendaciones': recomendaciones,
        'productos': productos,
    })

########################################Existencia en tiendas ###################################################
# apps/inventario/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Tienda, Producto, ExistenciasTienda
from .forms import ExistenciasTiendaForm

def agregar_existencias_tienda(request, tienda_id=None):
    """Vista para agregar o actualizar existencias de productos en una tienda"""
    tienda = None
    if tienda_id:
        tienda = get_object_or_404(Tienda, id=tienda_id)
    
    tiendas = Tienda.objects.all()
    productos = Producto.objects.all()
    
    if request.method == 'POST':
        tienda_id = request.POST.get('tienda')
        producto_id = request.POST.get('producto')
        cantidad = request.POST.get('cantidad')
        
        try:
            tienda_obj = get_object_or_404(Tienda, id=tienda_id)
            producto_obj = get_object_or_404(Producto, id=producto_id)
            cantidad = int(cantidad)
            
            # Verificar si ya existe una existencia para este producto en esta tienda
            existencia, created = ExistenciasTienda.objects.get_or_create(
                tienda=tienda_obj,
                producto=producto_obj,
                defaults={'cantidad': cantidad}
            )
            
            if not created:
                # Si ya existe, actualizar la cantidad (sumar)
                existencia.cantidad += cantidad
                existencia.save()
                messages.success(request, f'Se actualizaron las existencias de {producto_obj.nombre} en {tienda_obj.nombre}. Nueva cantidad: {existencia.cantidad}')
            else:
                messages.success(request, f'Se agregaron {cantidad} unidades de {producto_obj.nombre} a {tienda_obj.nombre}')
            
            return redirect('inventario:agregar_existencias_tienda')
            
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número válido')
        except Exception as e:
            messages.error(request, f'Error al agregar existencias: {str(e)}')
    
    # Obtener existencias actuales si hay una tienda seleccionada
    existencias_actuales = []
    if tienda:
        existencias_actuales = ExistenciasTienda.objects.filter(tienda=tienda).select_related('producto')
    
    context = {
        'tiendas': tiendas,
        'productos': productos,
        'tienda_seleccionada': tienda,
        'existencias_actuales': existencias_actuales,
    }
    
    return render(request, 'agregar_existencias_tienda.html', context)

def listar_existencias_tienda(request, tienda_id):
    """Vista para listar todas las existencias de una tienda específica"""
    tienda = get_object_or_404(Tienda, id=tienda_id)
    existencias = ExistenciasTienda.objects.filter(tienda=tienda).select_related('producto')
    
    context = {
        'tienda': tienda,
        'existencias': existencias,
    }
    
    return render(request, 'inventario/listar_existencias_tienda.html', context)

def obtener_existencias_tienda_ajax(request, tienda_id):
    """Vista AJAX para obtener existencias de una tienda"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            tienda = get_object_or_404(Tienda, id=tienda_id)
            existencias = ExistenciasTienda.objects.filter(tienda=tienda).select_related('producto')
            data = []
            for existencia in existencias:
                data.append({
                    'id': existencia.id,
                    'producto_id': existencia.producto.id,
                    'producto_nombre': existencia.producto.nombre,
                    'cantidad': existencia.cantidad,
                })
            return JsonResponse({'success': True, 'existencias': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Solicitud no válida'})

@require_http_methods(["POST"])
def actualizar_existencia_ajax(request):
    """Vista AJAX para actualizar existencia específica"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            tienda_id = request.POST.get('tienda_id')
            producto_id = request.POST.get('producto_id')
            nueva_cantidad = request.POST.get('cantidad')
            
            tienda = get_object_or_404(Tienda, id=tienda_id)
            producto = get_object_or_404(Producto, id=producto_id)
            nueva_cantidad = int(nueva_cantidad)
            
            existencia, created = ExistenciasTienda.objects.get_or_create(
                tienda=tienda,
                producto=producto,
                defaults={'cantidad': nueva_cantidad}
            )
            
            if not created:
                existencia.cantidad = nueva_cantidad
                existencia.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Existencia de {producto.nombre} actualizada correctamente a {nueva_cantidad} unidades'
            })
            
        except ValueError:
            return JsonResponse({'success': False, 'message': 'La cantidad debe ser un número válido'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al actualizar: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Solicitud no válida'})

def actualizar_existencia_tienda(request, existencia_id):
    """Vista para actualizar una existencia específica"""
    existencia = get_object_or_404(ExistenciasTienda, id=existencia_id)
    
    if request.method == 'POST':
        nueva_cantidad = request.POST.get('cantidad')
        try:
            existencia.cantidad = int(nueva_cantidad)
            existencia.save()
            messages.success(request, f'Existencia actualizada correctamente')
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número válido')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
    
    return redirect('inventario:listar_existencias_tienda', tienda_id=existencia.tienda.id)