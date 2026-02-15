from django import forms
from .models import Clientes

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Clientes
        fields = ['nombre', 'apellido', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre del cliente'
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apellido del cliente'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Teléfono de contacto'
            }),
        }