from django import forms
from .models import Producto, Tienda, Bodega

class TransferenciaForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tienda = forms.ModelChoiceField(
        queryset=Tienda.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    bodega = forms.ModelChoiceField(
        queryset=Bodega.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    numero_iteracion = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Número de Iteración"
    )