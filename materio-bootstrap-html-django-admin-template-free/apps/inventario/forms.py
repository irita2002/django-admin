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
    fecha_transferencia = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
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
    
    
    # apps/inventario/forms.py
from django import forms
from .models import ExistenciasTienda, Tienda, Producto

class ExistenciasTiendaForm(forms.ModelForm):
    class Meta:
        model = ExistenciasTienda
        fields = ['tienda', 'producto', 'cantidad']
        widgets = {
            'tienda': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True
            }),
            'producto': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'required': True,
                'placeholder': 'Ingrese la cantidad'
            })
        }
        labels = {
            'tienda': 'Tienda',
            'producto': 'Producto',
            'cantidad': 'Cantidad'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tienda'].queryset = Tienda.objects.all()
        self.fields['producto'].queryset = Producto.objects.all()
        
        # Agregar opciones vacías
        self.fields['tienda'].empty_label = "Seleccione una tienda"
        self.fields['producto'].empty_label = "Seleccione un producto"

class ActualizarExistenciaForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '1'
        })
    )