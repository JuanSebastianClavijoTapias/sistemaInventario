from django import forms
from .models import Proveedores

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedores
        fields = ['nombre', 'telefono', 'inicial', 'saldo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre del proveedor'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Teléfono de contacto'
            }),
            'inicial': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Pago inicial',
                'step': '0.01'
            }),
            'saldo': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Saldo pendiente',
                'step': '0.01'
            }),
        }