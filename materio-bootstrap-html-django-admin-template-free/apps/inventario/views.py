import datetime
from django.shortcuts import render, get_object_or_404
from .models import Producto, TransferenciaHistorial
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from io import BytesIO
from .forms import ExistenciasTiendaForm
from .models import Tienda, Producto, ExistenciasTienda
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Tienda, Bodega, Producto
from shapely.geometry import Point
import networkx as nx
import osmnx as ox
from .models import Circunscripcion
from .models import Bodega
from django.views.generic import DeleteView
from django.http import Http404, JsonResponse
from .models import Tienda
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.template.loader import render_to_string
from django.http import JsonResponse, Http404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Producto
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.template.defaulttags import register
from .models import Producto, Iteracion
from django.utils import timezone
from .models import ExistenciasTienda, ExistenciasBodegas, TransferenciaHistorial, Iteracion
from gettext import translation
from django.shortcuts import render, redirect
from .models import Producto, ExistenciasBodegas, ExistenciasTienda, Bodega, Tienda
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.db.models import Sum
from django.contrib import messages
from .forms import TransferenciaForm
from django.db import transaction
from web_project.template_helpers.theme import TemplateHelper
from .utils.map_generator import generar_mapa_offline
from .audit_decorators import *
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.shortcuts import render
from .forms import LoginForm
from web_project.template_helpers.theme import TemplateHelper
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import LoginForm
from django.contrib.auth.decorators import login_required


def sign_in(request):

    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('/')
        form = LoginForm()
        return render(request, 'auth_login_basic.html', {'form': form, })

    elif request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(
                    request, f'Hi {username.title()}, Bienvenido otra vez!')
                return redirect('/')

        # form is not valid or user is not authenticated
        messages.error(request, f'Contaseña o usuario incorrecto')
        return render(request, 'auth_login_basic.html', {'form': form, })


def sign_out(request):
    logout(request)
    messages.success(request, f'Estas deslogueado.')
    return redirect('login')


@login_required
@auditar_accion('VIEW', 'Producto', 'Comprobo existencias')
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


# @login_required
@login_required
@auditar_accion('TRANSFER', 'Producto', 'Transfirio existencias')
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
                    messages.error(
                        request, 'Cantidad insuficiente en la tienda')
                    return redirect('inventario:transferir_producto')

                with transaction.atomic():
                    # Actualizar existencias
                    stock=existencia_tienda.cantidad 
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
                        stock_previo=stock,
                        fecha_transferencia=fecha_transferencia,
                        tienda_destino=tienda
                    )

                messages.success(
                    request, f'Transferencia a {bodega.nombre} registrada en Iteración {numero_iteracion}')
                return redirect('inventario:transferir_producto')

            except ExistenciasTienda.DoesNotExist:
                messages.error(request, 'El producto no existe en esta tienda')
                return redirect('inventario:transferir_producto')

    else:
        form = TransferenciaForm()

    return render(request, 'transferencia.html', {'form': form, 'layout_path': TemplateHelper.set_layout("layout_blank.html"), })




@login_required
@auditar_accion('VIEW', 'Producto', 'Vio existencias')
def get_item(dictionary, key):
    return dictionary.get(key, False)


@login_required
@auditar_accion('VIEW', 'Producto', 'Vio existencias')
def iteraciones_por_producto(request):
    producto_seleccionado = None
    iteracion_id = 0
    iteraciones = {}
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
        transferencia = TransferenciaHistorial.objects.filter(
            producto=producto_seleccionado, iteracion=iteraciones[0].id).order_by('fecha_transferencia')
    except:
        transferencia = TransferenciaHistorial.objects.filter(
            producto=producto_seleccionado, iteracion=iteracion_id).order_by('fecha_transferencia')
    iteracion_t = Iteracion.objects.all

    return render(request, 'iteraciones_producto.html', {
        'productos': productos,
        'producto_seleccionado': producto_seleccionado,
        'iteraciones_agrupadas': iteraciones_agrupadas,
        'iteracion_t': iteracion_t,
        'bodegas': bodegas,
        'transferencias': transferencia,
        'layout_path': TemplateHelper.set_layout("layout_blank.html"),

    })


@login_required
@auditar_accion('VIEW', 'Bodega', 'Vio bodegas')
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


@auditar_accion('VIEW', 'Bodega', 'Vio mapa')
def mapa_principal(request):
    tiendas = Tienda.objects.all()
    bodegas = Bodega.objects.all()
    productos = Producto.objects.all()
    mapa_html = generar_mapa_offline(list(tiendas) + list(bodegas))
    return render(request, 'map.html', {'mapa': mapa_html, 'tiendas': tiendas, 'bodegas': bodegas, 'productos': productos})

# ///////////////////Producto////////////////////////


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
                total=Sum('existenciastienda__cantidad') +
                Sum('existenciasbodegas__cantidad'),
            )
            .order_by('nombre')
        )


class ProductoDetailView(DetailView):
    model = Producto
    template_name = "producto/producto_detail.html"
    context_object_name = "producto"



# ———————————————————————————————
# 1) Listado de Productos
# ———————————————————————————————


# ———————————————————————————————
# 2) Crear Producto (AJAX)
# ———————————————————————————————
class ProductoCreateView(CreateView):
    model = Producto
    fields = ["nombre", "primera_necesidad"]  # Ajusta según tus campos reales
    template_name = "producto/producto_form.html"
    success_url = reverse_lazy("inventario:list")

    def form_invalid(self, form):
        # Si viene AJAX y no es válido, devolvemos solo el fragmento con errores
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            context = self.get_context_data(form=form, object=None)
            html = render_to_string(
                self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    @auditar_accion('CREATE', 'Producto', 'Creo producto')
    def form_valid(self, form):
        # Si viene AJAX y es válido, devolvemos { success: True }
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    @auditar_accion('VIEW', 'Producto', 'Vio producto')
    def get(self, request, *args, **kwargs):
        # Si es AJAX, enviamos solo el fragmento de formulario (vacío)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = None
            form = self.get_form()
            context = self.get_context_data(form=form, object=None)
            html = render_to_string(
                self.template_name, context, request=request)
            return JsonResponse({"success": True, "html": html})
        # Si no es AJAX, comportamiento normal
        return super().get(request, *args, **kwargs)


# ———————————————————————————————
# 3) Editar Producto (AJAX)
# ———————————————————————————————
class ProductoUpdateView(UpdateView):
    model = Producto
    fields = ["nombre", "primera_necesidad"]  # Mismos campos que en CreateView
    template_name = "producto/producto_form.html"
    success_url = reverse_lazy("inventario:list")

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            context = self.get_context_data(
                form=form, object=self.get_object())
            html = render_to_string(
                self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    @auditar_accion('UPDATE', 'Producto', 'Actualizo producto')
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    @auditar_accion('VIEW', 'Producto', 'Vio producto')
    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = self.get_object()
            form = self.get_form()
            context = self.get_context_data(form=form, object=self.object)
            html = render_to_string(
                self.template_name, context, request=request)
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

    @auditar_accion('DELETE', 'Producto', 'Borro producto')
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


# ///////////////////Tiendas////////////////////////


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
            html = render_to_string(
                self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    @auditar_accion('CREATE', 'Tienda', 'Creo Tienda')
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
            html = render_to_string(
                self.template_name, context, request=request)
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
            context = self.get_context_data(
                form=form, object=self.get_object())
            html = render_to_string(
                self.template_name, context, request=self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    @auditar_accion('UPDATE', 'Tienda', 'Actualizo Tienda')
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
            html = render_to_string(
                self.template_name, context, request=request)
            return JsonResponse({"success": True, "html": html})
        return super().get(request, *args, **kwargs)


class TiendaDeleteView(DeleteView):
    model = Tienda
    # Vista completa para peticiones no-AJAX
    template_name = "tienda/tienda_confirm_delete.html"
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

    @auditar_accion('DELETE', 'Tienda', 'Borrar Tienda')
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


# ///////////////////Bodegas////////////////////////


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
    fields = ["nombre", "cp", "cantidad_nucleos",
              "latitud", "longitud", "orden"]
    template_name = "bodega/bodega_form.html"
    success_url = reverse_lazy("inventario:bodega_list")

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(
                form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    @auditar_accion('CREATE', 'Bodega', 'Creo una  Bodega')
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return response

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.get_form()
            html = render_to_string(self.template_name, {
                                    'form': form, 'object': None}, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)


class BodegaUpdateView(UpdateView):
    model = Bodega
    fields = ["nombre", "cp", "cantidad_nucleos",
              "latitud", "longitud", "orden"]
    template_name = "bodega/bodega_form.html"
    success_url = reverse_lazy("inventario:bodega_list")

    def form_invalid(self, form):
        # si es AJAX, devolvemos el formulario con errores
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(
                form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    @auditar_accion('UPDATE', 'Bodega', 'Actualizo una  Bodega')
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
            html = render_to_string(self.template_name, {
                                    'form': form, 'object': self.object}, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)



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

    @auditar_accion('DELETE', 'Bodega', 'Borro una  Bodega')
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


# ///////////////////Circunscripcion////////////////////////


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
            html = render_to_string(self.template_name, self.get_context_data(
                form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    @auditar_accion('CREATE', 'Circunscripcion', 'Creo una Circunscripcion')
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
            html = render_to_string(
                self.template_name, context, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)


class CircunscripcionUpdateView(UpdateView):
    model = Circunscripcion
    fields = ["nombre", "ancianos", "ninos", "embarazadas"]
    template_name = "circunscripcion/circunscripcion_form.html"
    success_url = reverse_lazy("inventario:circunscripcion_list")

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, self.get_context_data(
                form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    @auditar_accion('UPDATE', 'Circunscripcion', 'Actualizo una Circunscripcion')
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
            html = render_to_string(
                self.template_name, context, request=request)
            return JsonResponse({'success': True, 'html': html})
        return super().get(request, *args, **kwargs)


class CircunscripcionDeleteView(DeleteView):
    model = Circunscripcion
    # Para peticiones normales
    template_name = "circunscripcion/circunscripcion_confirm_delete.html"
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

    @auditar_accion('DELETE', 'Circunscripcion', 'Borro una Circunscripcion')
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


################################## Mapa##################################################
# tuapp/views.py
def recomendar_bodega(tienda_origen, producto, alfa=0.7, beta=0.3, gamma=0.5):
    """
    Recomienda bodegas para transferencia considerando:
    - Necesidad de la bodega
    - Distancia desde tienda origen
    - Población vulnerable (si es producto de primera necesidad)

    Args:
        tienda_origen: ID de la tienda origen
        producto: Instancia del producto
        alfa: Peso para necesidad (default 0.7)
        beta: Peso para distancia (default 0.3) 
        gamma: Peso para vulnerables cuando es primera necesidad (default 0.5)
    """
    # 1. Obtener ubicación de tienda
    tienda = Tienda.objects.get(id=tienda_origen)

    lat0 = float(tienda.latitud)
    lon0 = float(tienda.longitud)
    print(str(lat0)+"+" + str(lon0))

    # 2. Descargar grafo vial y proyectar
    G = ox.graph_from_point((lat0, lon0), dist=3000, network_type='drive')
    G_proj = ox.project_graph(G)

    geom0, _ = ox.projection.project_geometry(
        Point(lon0, lat0), to_crs=G_proj.graph['crs'])
    nodo_origen = ox.distance.nearest_nodes(G_proj, geom0.x, geom0.y)

    # 3. Calcular necesidad, distancia y vulnerables por bodega
    from apps.inventario.models import Bodega, TransferenciaHistorial
    bodegas = Bodega.objects.select_related('cp').all()

    resultados = []

    max_necesidad = 0
    max_distancia = 1  # evitar división por cero
    max_vulnerables = 1  # evitar división por cero

    # Primera pasada: calcular valores y encontrar máximos
    for bodega in bodegas:
        lat_b = bodega.latitud
        lon_b = bodega.longitud

        geom_b, _ = ox.projection.project_geometry(
            Point(lon_b, lat_b), to_crs=G_proj.graph['crs'])
        nodo_b = ox.distance.nearest_nodes(G_proj, geom_b.x, geom_b.y)

        distancia = nx.shortest_path_length(
            G_proj, nodo_origen, nodo_b, weight='length')  # en metros

        entregado = TransferenciaHistorial.objects.filter(
            producto=producto,
            bodega=bodega
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        necesidad = max(bodega.cantidad_nucleos - entregado, 0)
        if necesidad==0:
            pass
        else:
        # Obtener población vulnerable de la circunscripción
            vulnerables = bodega.cp.total_vulnerables if bodega.cp else 0

            max_necesidad = max(max_necesidad, necesidad)
            max_distancia = max(max_distancia, distancia)
            max_vulnerables = max(max_vulnerables, vulnerables)

            resultados.append({
                'bodega': bodega,
                'necesidad': necesidad,
                'distancia': distancia,
                'vulnerables': vulnerables,
                'latitud': lat_b,
                'longitud': lon_b
            })
    # 4. Normalizar y calcular score
    recomendaciones = []
    es_primera_necesidad = producto.primera_necesidad

    for r in resultados:
        necesidad_n = r['necesidad'] / max_necesidad if max_necesidad else 0
        distancia_n = r['distancia'] / max_distancia if max_distancia else 0
        vulnerables_n = r['vulnerables'] / \
            max_vulnerables if max_vulnerables else 0

        if es_primera_necesidad:
            # Para productos de primera necesidad, ajustar pesos para priorizar vulnerables
            # Reducir alfa y beta para dar espacio a gamma
            alfa_adj = alfa * 0.6  # Reducir peso de necesidad
            beta_adj = beta * 0.6  # Reducir peso de distancia
            score = alfa_adj * necesidad_n - beta_adj * distancia_n + gamma * vulnerables_n
        else:
            # Para productos normales, usar la fórmula original
            score = alfa * necesidad_n - beta * distancia_n

        recomendaciones.append({
            'bodega': r['bodega'],
            'necesidad': r['necesidad'],
            'distancia_m': round(r['distancia']),
            'vulnerables': r['vulnerables'],
            'score': round(score, 4),
            'es_primera_necesidad': es_primera_necesidad,
            'latitud': r['latitud'],
            'longitud': r['longitud'],
        })

    recomendaciones = sorted(
        recomendaciones, key=lambda x: x['score'], reverse=True)

    # Información adicional para debug
    if es_primera_necesidad:
        print(f"Producto de PRIMERA NECESIDAD: {producto.nombre}")
        print("Priorizando bodegas con mayor población vulnerable")
    else:
        print(f"Producto regular: {producto.nombre}")

    print(recomendaciones)

    return recomendaciones


@login_required
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

        # Generar mapa con la tienda como origen
        mapa_html = generar_mapa_offline(
            ubicaciones=bodegas,
            direccion_origen=f"{tienda_origen.latitud},{tienda_origen.longitud}"
        )
        print(f"GET parameters: {dict(request.GET)}")
        # Obtener producto seleccionado si existe
        if 'producto_id' in request.GET:
            try:
                producto_id = request.GET['producto_id']
                if producto_id:  # Verificar que no esté vacío
                    producto_seleccionado = get_object_or_404(
                        Producto, id=producto_id)
                    print(f"Producto seleccionado: {producto_seleccionado}")

                    # Solo llamar recomendar_bodega si hay tienda Y producto
                    try:
                        recomendaciones = recomendar_bodega(
                            tienda_id, producto_seleccionado)
                        print(
                            f"Recomendaciones generadas: {len(recomendaciones)}")

                        # Agregar información adicional para el template
                        for rec in recomendaciones:
                            rec['distancia_km'] = round(
                                rec['distancia_m'] / 1000, 2)

                    except Exception as e:
                        messages.error(
                            request, f'Error al generar recomendaciones: {str(e)}')
                        print(f"Error en recomendar_bodega: {e}")
                        recomendaciones = []

            except (ValueError, Producto.DoesNotExist) as e:
                messages.error(request, 'Producto no válido seleccionado')
                print(f"Error con producto: {e}")
                producto_seleccionado = None

    else:
        # sin tienda seleccionada, mapa centrado en coordenadas por defecto
        mapa_html = generar_mapa_offline(ubicaciones=bodegas)
        # NO llamamos recomendar_bodega cuando no hay tienda seleccionada
    print(recomendaciones)
    context = {
        'Bodega': bodegas,
        'tiendas': tiendas,
        'mapa': mapa_html,
        'tienda_seleccionada': tienda_id,
        'producto_seleccionado': producto_seleccionado,
        'recomendaciones': recomendaciones,
        'productos': productos,
        # Información adicional para el template
        'tiene_recomendaciones': len(recomendaciones) > 0,
        'es_primera_necesidad': producto_seleccionado.primera_necesidad if producto_seleccionado else False,
    }

    return render(request, 'map.html', context)


######################################## Existencia en tiendas ###################################################
# apps/inventario/views.py
@login_required
@auditar_accion('CREATE', 'ExistenciasTienda', 'Actualizo ExistenciasTienda')
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
                messages.success(
                    request, f'Se actualizaron las existencias de {producto_obj.nombre} en {tienda_obj.nombre}. Nueva cantidad: {existencia.cantidad}')
            else:
                messages.success(
                    request, f'Se agregaron {cantidad} unidades de {producto_obj.nombre} a {tienda_obj.nombre}')

            return redirect('inventario:agregar_existencias_tienda')

        except ValueError:
            messages.error(request, 'La cantidad debe ser un número válido')
        except Exception as e:
            messages.error(request, f'Error al agregar existencias: {str(e)}')

    # Obtener existencias actuales si hay una tienda seleccionada
    existencias_actuales = []
    if tienda:
        existencias_actuales = ExistenciasTienda.objects.filter(
            tienda=tienda).select_related('producto')

    context = {
        'tiendas': tiendas,
        'productos': productos,
        'tienda_seleccionada': tienda,
        'existencias_actuales': existencias_actuales,
    }

    return render(request, 'agregar_existencias_tienda.html', context)


@login_required
@auditar_accion('VIEW', 'ExistenciasTienda', 'Ver ExistenciasTienda')
def listar_existencias_tienda(request, tienda_id):
    """Vista para listar todas las existencias de una tienda específica"""
    tienda = get_object_or_404(Tienda, id=tienda_id)
    existencias = ExistenciasTienda.objects.filter(
        tienda=tienda).select_related('producto')

    context = {
        'tienda': tienda,
        'existencias': existencias,
    }

    return render(request, 'inventario/listar_existencias_tienda.html', context)


@login_required
def obtener_existencias_tienda_ajax(request, tienda_id):
    """Vista AJAX para obtener existencias de una tienda"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            tienda = get_object_or_404(Tienda, id=tienda_id)
            existencias = ExistenciasTienda.objects.filter(
                tienda=tienda).select_related('producto')
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


@login_required
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


@login_required
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


def generar_pdf_desde_html(html_content):
    """
    Dado un string de HTML, lo convierte a PDF usando xhtml2pdf (pisa)
    y devuelve un HttpResponse con el PDF.
    """
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode('utf-8')), result)
    if pdf.err:
        return None
    return result.getvalue()


def informe_ventas_pdf(request, producto_id, fecha_str=None):
    """
    Vista que genera un informe de ventas (transferencias) de un producto
    en una fecha dada y devuelve un PDF.
    - parametro producto_id: ID del producto a consultar
    - parametro fecha_str (opcional): cadena "YYYY-MM-DD". Si no se da, se usa hoy.
    """
    # 1. Definir la fecha del reporte:
    if fecha_str:
        try:
            fecha_reporte = datetime.datetime.strptime(
                fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return HttpResponse("Formato de fecha inválido. Usa YYYY-MM-DD.", status=400)
    else:
        # Si no se pasa fecha, usar hoy
        fecha_reporte = timezone.now().date()

    # 2. Obtener el objeto Producto o devolver 404 si no existe
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return HttpResponse(f"Producto {producto_id} no encontrado", status=404)

    # 3. Filtrar las transferencias del producto en esa fecha (ignoro hora)
    transferencias = (
        TransferenciaHistorial.objects
        .filter(producto=producto, fecha_transferencia__date=fecha_reporte)
        .select_related('bodega__cp', 'tienda_destino')
    )

    # 4. Preparar la lista de 'datos' para la plantilla
    datos_informe = []
    for transferencia in transferencias:
        datos_informe.append({
            'circunscripcion': transferencia.bodega.cp.nombre if transferencia.bodega and transferencia.bodega.cp else "",
            'bodega': transferencia.bodega.nombre if transferencia.bodega else "",
            'clientes': transferencia.cantidad or 0,
            'producto': producto.nombre,
            'tienda': transferencia.tienda_destino.nombre if transferencia.tienda_destino else "",
            'cadena': transferencia.tienda_destino.tipo if transferencia.tienda_destino else ""
        })

    # 5. Calcular total de cantidades
    total_cantidad = transferencias.aggregate(
        total=Sum('cantidad'))['total'] or 0

    # 6. Preparar el contexto para la plantilla
    contexto = {
        'titulo': f"VENTA {producto.nombre} {fecha_reporte.strftime('%A %d de %B %Y').upper()}",
        # Por ejemplo, la fecha de distribución es el día anterior
        'fecha_distribucion': (fecha_reporte - datetime.timedelta(days=1)).strftime('%d de %B %Y'),
        'datos': datos_informe,
        'total_cantidad': total_cantidad,
        'fecha_generacion': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    # 7. Renderizar la plantilla a HTML
    template = get_template('informe_ventas.html')
    html_content = template.render(contexto)

    # 8. Convertir HTML a PDF
    pdf_bytes = generar_pdf_desde_html(html_content)
    if pdf_bytes is None:
        return HttpResponse("Error al generar el PDF", status=500)

    # 9. Devolver el PDF en un HttpResponse
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"informe_ventas_{producto.nombre}_{fecha_reporte}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def formulario_informe_ventas(request):
    """
    Muestra el formulario para seleccionar producto y fecha
    y redirige a la vista que genera el PDF.
    """
    productos = Producto.objects.all()
    return render(request, 'informe_formulario.html', {'productos': productos})


def informe_ventas_pdf_form(request):
    """
    Recibe parámetros GET (?producto=ID&fecha=YYYY-MM-DD) y llama
    a la vista de generación de informe.
    """
    producto_id = request.GET.get('producto')
    fecha_str = request.GET.get('fecha')

    if not producto_id or not fecha_str:
        return HttpResponse("Parámetros incompletos", status=400)

    # Redirige a la vista ya existente con esos parámetros
    return informe_ventas_pdf(request, producto_id=producto_id, fecha_str=fecha_str)

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Producto, TransferenciaHistorial

from django.shortcuts import render, get_object_or_404
from .models import Producto, TransferenciaHistorial, Tienda, Bodega
from django.db.models import Q

def transferencias_por_producto(request):
    """
    Vista que muestra el historial de transferencias, por defecto todas,
    y permite filtrar por producto, tienda, bodega y circunscripción.
    """
    # Obtener todos los posibles valores para los selects de filtro
    productos = Producto.objects.all()
    tiendas = Tienda.objects.all()
    bodegas = Bodega.objects.select_related('cp').all()
    circunscripciones = Circunscripcion.objects.all()

    # Leer parámetros GET de filtro
    producto_id = request.GET.get('producto_id')  # puede ser None o '' si no se seleccionó
    tienda_id = request.GET.get('tienda_id')
    bodega_id = request.GET.get('bodega_id')
    circunscripcion_id = request.GET.get('circunscripcion_id')

    # Construir el queryset inicial: todas las transferencias, con select_related para optimizar
    qs = TransferenciaHistorial.objects.select_related(
        'producto', 'tienda_destino', 'bodega__cp'
    ).order_by('-fecha_transferencia')

    # Variables para preselección en el template
    producto_seleccionado = None
    tienda_seleccionada = None
    bodega_seleccionada = None
    circunscripcion_seleccionada = None

    # Aplicar filtros condicionalmente
    # Filtrar por producto
    if producto_id:
        try:
            producto_seleccionado = get_object_or_404(Producto, id=producto_id)
            qs = qs.filter(producto=producto_seleccionado)
        except ValueError:
            # Si producto_id no es un entero válido, ignorar filtro
            producto_seleccionado = None

    # Filtrar por tienda
    if tienda_id:
        try:
            tienda_seleccionada = get_object_or_404(Tienda, id=tienda_id)
            qs = qs.filter(tienda_destino=tienda_seleccionada)
        except ValueError:
            tienda_seleccionada = None

    # Filtrar por bodega
    if bodega_id:
        try:
            bodega_seleccionada = get_object_or_404(Bodega, id=bodega_id)
            qs = qs.filter(bodega=bodega_seleccionada)
        except ValueError:
            bodega_seleccionada = None

    # Filtrar por circunscripción (relacionada a la bodega)
    if circunscripcion_id:
        try:
            circunscripcion_seleccionada = get_object_or_404(Circunscripcion, id=circunscripcion_id)
            qs = qs.filter(bodega__cp=circunscripcion_seleccionada)
        except ValueError:
            circunscripcion_seleccionada = None

    # Finalmente, obtenemos la lista resultante
    transferencias = qs

    contexto = {
        'productos': productos,
        'tiendas': tiendas,
        'bodegas': bodegas,
        'circunscripciones': circunscripciones,
        # Valores seleccionados para preselección en el formulario
        'producto_seleccionado': producto_seleccionado,
        'tienda_seleccionada': tienda_seleccionada,
        'bodega_seleccionada': bodega_seleccionada,
        'circunscripcion_seleccionada': circunscripcion_seleccionada,
        'transferencias': transferencias,
    }
    return render(request, 'transferencias_producto.html', contexto)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import UserEditForm  # y UserPasswordChangeForm si lo defines
from .templatetags.permissions import usuario_es_admin
from django.contrib.auth.decorators import login_required

@login_required
@usuario_es_admin
def user_list(request):
    """
    Lista de usuarios con paginación y búsqueda opcional.
    """
    query = request.GET.get('q', '')
    users_qs = User.objects.all().order_by('username')
    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    paginator = Paginator(users_qs, 20)  # 20 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    contexto = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'configuracion/user_list.html', contexto)

@login_required
@usuario_es_admin
def user_create(request):
    """
    Crear un nuevo usuario. Usa UserCreationForm y luego asignar roles.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        # UserCreationForm tiene campos username, password1, password2.
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # o según lógica
            user.save()
            messages.success(request, f"Usuario '{user.username}' creado exitosamente. Ahora asigna roles si deseas.")
            return redirect('inventario:user_edit', pk=user.pk)
    else:
        form = UserCreationForm()
    return render(request, 'configuracion/user_create.html', {'form': form})

@login_required
@usuario_es_admin
def user_edit(request, pk):
    """
    Editar datos de usuario y asignar grupos.
    """
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            # username es readonly, no cambia
            user = form.save(commit=False)
            user.save()
            # grupos:
            groups = form.cleaned_data.get('groups')
            if groups is not None:
                user.groups.set(groups)
            messages.success(request, f"Usuario '{user.username}' actualizado correctamente.")
            return redirect('inventario:user_list')
    else:
        form = UserEditForm(instance=user_obj)
    return render(request, 'configuracion/user_edit.html', {
        'form': form,
        'user_obj': user_obj,
    })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages

@login_required
@usuario_es_admin
def user_change_password(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    print("DEBUG: Entrando en user_change_password para usuario:", user_obj.username)
    if request.method == 'POST':
        form = AdminPasswordChangeForm(user_obj, request.POST)
    else:
        form = AdminPasswordChangeForm(user_obj)
    # Depuración: imprimir campos del form
    print("DEBUG: form.fields keys:", list(form.fields.keys()))
    for name, field in form.fields.items():
        print(f"DEBUG: campo {name}: {field}")
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"Contraseña de '{user_obj.username}' cambiada correctamente.")
            return redirect('inventario:user_list')
        else:
            print("DEBUG: form.errors:", form.errors)
    return render(request, 'configuracion/user_change_password.html', {
        'form': form,
        'user_obj': user_obj,
    })


@login_required
@usuario_es_admin
def user_delete(request, pk):
    """
    Eliminar usuario (opcional). Pide confirmación.
    """
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        # Evitar que se elimine a sí mismo
        if request.user == user_obj:
            messages.error(request, "No puedes eliminar tu propia cuenta desde aquí.")
            return redirect('inventario:user_list')
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f"Usuario '{username}' eliminado.")
        return redirect('inventario:user_list')
    return render(request, 'configuracion/user_confirm_delete.html', {
        'user_obj': user_obj,
    })
