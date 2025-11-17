from rest_framework import serializers
from .models import (
    Usuario, Cliente, Vendedor, Marca, Modelo, Vehiculo, Accesorio,
    ModeloAccesorio, Oferta, Cotizacion, CotizacionVehiculo,
    CotizacionAccesorio, Reserva, Venta, Pago
)
from django.contrib.auth import authenticate

# ==================== USUARIOS Y AUTH ====================

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'tipo_usuario', 'is_active']
        read_only_fields = ['id', 'is_active']

class RegistroClienteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    
    class Meta:
        model = Cliente
        fields = ['dni', 'nombre', 'apellido', 'fecha_nacimiento', 'direccion', 'email', 'password']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            email=email,
            password=password,
            tipo_usuario='CLIENTE'
        )
        
        # Crear cliente
        cliente = Cliente.objects.create(usuario=usuario, **validated_data)
        return cliente

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Credenciales inválidas")

# ==================== PRODUCTOS ====================

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'

class ModeloSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(source='marca.nombre', read_only=True)
    
    class Meta:
        model = Modelo
        fields = '__all__'

class OfertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oferta
        fields = '__all__'

class VehiculoSerializer(serializers.ModelSerializer):
    modelo_nombre = serializers.CharField(source='modelo.nombre', read_only=True)
    marca_nombre = serializers.CharField(source='modelo.marca.nombre', read_only=True)
    precio_con_oferta = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehiculo
        fields = '__all__'
    
    def get_precio_con_oferta(self, obj):
        return obj.get_precio_con_oferta()

class AccesorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accesorio
        fields = '__all__'

class ModeloAccesorioSerializer(serializers.ModelSerializer):
    accesorio_nombre = serializers.CharField(source='accesorio.nombre', read_only=True)
    
    class Meta:
        model = ModeloAccesorio
        fields = '__all__'

# ==================== COTIZACIONES ====================

class CotizacionVehiculoSerializer(serializers.ModelSerializer):
    vehiculo_detalle = VehiculoSerializer(source='vehiculo', read_only=True)
    
    class Meta:
        model = CotizacionVehiculo
        fields = ['id', 'vehiculo', 'vehiculo_detalle', 'precio_unitario']

class CotizacionAccesorioSerializer(serializers.ModelSerializer):
    accesorio_detalle = AccesorioSerializer(source='accesorio', read_only=True)
    
    class Meta:
        model = CotizacionAccesorio
        fields = ['id', 'accesorio', 'accesorio_detalle', 'precio_unitario', 'cotizacion_vehiculo']

class CotizacionSerializer(serializers.ModelSerializer):
    vehiculos = CotizacionVehiculoSerializer(many=True, read_only=True)
    accesorios = CotizacionAccesorioSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cotizacion
        fields = '__all__'
        read_only_fields = ['fecha_hora_generada', 'importe_final', 'valida', 'fecha_hora_vencimiento']


class SimularCotizacionSerializer(serializers.Serializer):
    vehiculos = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=1,
        max_length=2
    )

class GenerarCotizacionSerializer(serializers.Serializer):
    vehiculos = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=1,
        max_length=2
    )
    cliente_id = serializers.UUIDField(required=False)  # Para vendedores

# ==================== RESERVAS Y VENTAS ====================

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
        read_only_fields = ['nro_pago', 'fecha_hora_generado']

class ReservaSerializer(serializers.ModelSerializer):
    pago_detalle = PagoSerializer(source='pago', read_only=True)
    
    class Meta:
        model = Reserva
        fields = '__all__'
        read_only_fields = ['nro_reserva', 'fecha_hora_generada', 'estado', 'fecha_hora_vencimiento']

class VentaSerializer(serializers.ModelSerializer):
    pago_detalle = PagoSerializer(source='pago', read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.nombre', read_only=True)
    
    class Meta:
        model = Venta
        fields = '__all__'
        read_only_fields = ['nro_venta', 'fecha_hora_generada', 'concretada', 'comision']

class RealizarPagoSerializer(serializers.Serializer):
    importe = serializers.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = serializers.ChoiceField(choices=['TARJETA', 'EFECTIVO', 'TRANSFERENCIA'])
