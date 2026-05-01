from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Venta, DetalleVenta, Cobro
from apps.clientes.models import Clientes
from apps.productos.models import Productos


class VentaForm(forms.ModelForm):
    """Formulario para crear/editar una venta"""
    
    class Meta:
        model = Venta
        fields = ['cliente', 'tipo_pago', 'metodo_pago']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-control',
                'id': 'cliente-select',
                'required': True,
            }),
            'tipo_pago': forms.Select(
                choices=Venta.TIPO_PAGO_CHOICES,
                attrs={
                    'class': 'form-control',
                    'id': 'tipo-pago',
                }
            ),
            'metodo_pago': forms.Select(
                choices=[
                    ('efectivo', 'Efectivo'),
                    ('tarjeta', 'Tarjeta'),
                ],
                attrs={
                    'class': 'form-control',
                    'id': 'metodo-pago',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Clientes.objects.all()
        self.fields['cliente'].label = "Cliente"
        self.fields['tipo_pago'].label = "Tipo de Pago"
        self.fields['metodo_pago'].label = "Método de Pago"


class DetalleVentaForm(forms.Form):
    """Formulario dinámico para agregar/editar productos en una venta"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    producto = forms.ModelChoiceField(
        queryset=Productos.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control producto-select',
            'required': True,
        }),
        label="Producto"
    )
    
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control cantidad-input',
            'placeholder': 'Cantidad',
            'required': True,
        }),
        label="Cantidad (kg)"
    )
    
    precio_venta = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control precio-input',
            'placeholder': 'Precio de venta',
            'step': '0.01',
            'required': True,
        }),
        label="Precio de Venta ($)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        precio_venta = cleaned_data.get('precio_venta')
        
        if cantidad and cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")
        
        if precio_venta and precio_venta <= 0:
            raise ValidationError("El precio de venta debe ser mayor a 0")
        
        return cleaned_data


class CobroForm(forms.ModelForm):
    """Formulario para registrar pagos/abonos en ventas a crédito"""
    
    class Meta:
        model = Cobro
        fields = ['monto']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto del abono',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
        }
        labels = {
            'monto': 'Monto del Abono ($)',
        }
    
    def __init__(self, venta=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.venta = venta
    
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        
        if not monto or monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0")
        
        if self.venta:
            saldo_pendiente = self.venta.saldo_pendiente
            if monto > saldo_pendiente:
                raise ValidationError(
                    f"El monto no puede exceder el saldo pendiente (${saldo_pendiente:,.2f})"
                )
        
        return monto


class EditarVentaForm(forms.Form):
    """Formulario para editar una venta existente (agregar productos o aumentar cantidades)"""
    
    accion = forms.ChoiceField(
        choices=[
            ('agregar_producto', 'Agregar nuevo producto'),
            ('aumentar_cantidad', 'Aumentar cantidad de producto existente'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label="¿Qué desea hacer?"
    )
    
    producto = forms.ModelChoiceField(
        queryset=Productos.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label="Producto"
    )
    
    cantidad = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cantidad (kg)',
        }),
        label="Cantidad (kg)"
    )
    
    precio_venta = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Precio de venta',
            'step': '0.01',
        }),
        label="Precio de Venta ($)"
    )
    
    def __init__(self, venta=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.venta = venta
    
    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        precio_venta = cleaned_data.get('precio_venta')
        
        if accion and producto:
            if not cantidad or cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor a 0")
            
            if not precio_venta or precio_venta <= 0:
                raise ValidationError("El precio de venta debe ser mayor a 0")
            
            # Si la acción es aumentar cantidad, verificar que el producto ya está en la venta
            if accion == 'aumentar_cantidad' and self.venta:
                existe = self.venta.detalles.filter(producto=producto).exists()
                if not existe:
                    raise ValidationError(
                        f"El producto {producto.nombre} no está en esta venta. "
                        "Use 'Agregar nuevo producto' para añadirlo."
                    )
        
        return cleaned_data
