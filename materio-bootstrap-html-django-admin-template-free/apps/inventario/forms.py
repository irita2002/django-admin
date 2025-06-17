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
class LoginForm(forms.Form):
    username = forms.CharField(max_length=65)
    password = forms.CharField(max_length=65, widget=forms.PasswordInput)
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AdminPasswordChangeForm

class UserEditForm(forms.ModelForm):
    """
    Formulario para editar campos de User y asignar grupos (roles).
    """
    # Añadimos campo para roles: múltiple selección de grupos
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    # Opcional: campos adicionales (first_name, last_name, email)
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput(), label="Activo")
    is_staff = forms.BooleanField(required=False, widget=forms.CheckboxInput(), label="¿Es staff?")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active','is_staff', 'groups']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            # si no quieres que username sea editable; si deseas que sea editable, quita 'readonly'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si quieres que username sea editable, comenta la línea readonly en widgets Meta.
        # Pre-seleccionar grupos: Django hace automáticamente si instance tiene grupos.
        # Ajustar clases Bootstrap:
        # Los campos ya tienen widget con 'form-control' o 'form-select'.
        # Si usas widget_tweaks, podrías omitir attrs y añadir clases en template.
        # Aquí garantizamos que todos tengan clase form-control excepto groups que usa SelectMultiple con form-select.
        # is_active es checkbox.
        # Si deseas cambiar etiqueta de username:
        self.fields['username'].label = "Nombre de usuario"
        self.fields['groups'].label = "Roles (Grupos)"
        self.fields['is_staff'].help_text = "Marcar si este usuario puede acceder al admin y crear nuevos usuarios."
class UserPasswordChangeForm(AdminPasswordChangeForm):
    """
    Hereda AdminPasswordChangeForm, que pide nueva contraseña y confirmación.
    """
    pass
