from django.shortcuts import render
from .models import Producto
from django.views.generic import TemplateView
from web_project import TemplateLayout

class inventario(TemplateView):
    template_name = 'inventario.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
    
        # Acceso a datos del modelo
        mis_productos = Producto.objects.all()
        context['productos'] = mis_productos

        return context


class detalles(TemplateView):
    template_name = 'detalles.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
    
        # Acceso a datos del modelo
        mis_productos = Producto.objects.all()
        context['productos'] = mis_productos

        return context