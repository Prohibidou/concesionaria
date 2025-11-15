"""
Modelos del Sistema FLY CAR - Gestión de Concesionaria
Basado en la documentación del proyecto

Modelos implementados según:
- G1 - Modelo de datos.pdf
- G1 - Modelo conceptual de dominio actualizado
- G1 - SRS-830.pdf
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal
import uuid


# ==================== MANAGERS ====================

class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario"""
    
    def create_user(self, email, password, tipo_usuario, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, tipo_usuario=tipo_usuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        return self.create_user(
            email=email,
            password=password,
            tipo_usuario='ADMINISTRADOR',
            is_staff=True,
            is_superuser=True,
            **extra_fields
        )


# ==================== MODELOS PRINCIPALES ====================

class Usuario(AbstractBaseUser, PermissionsMixin):
    """Modelo base para todos los usuarios del sistema"""
    
    TIPO_USUARIO_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('VENDEDOR', 'Vendedor'),
        ('CLIENTE', 'Cliente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.email} ({self.tipo_usuario})"


class Cliente(models.Model):
    """Modelo para clientes del sistema"""
    
    dni_validator = RegexValidator(
        regex=r'^\d{8}$',
        message='El DNI debe tener exactamente 8 dígitos'
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dni = models.CharField(max_length=8, unique=True, validators=[dni_validator])
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    direccion = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='cliente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - DNI: {self.dni}"


class Vendedor(models.Model):
    """Modelo para vendedores del sistema"""
    
    dni_validator = RegexValidator(
        regex=r'^\d{8}$',
        message='El DNI debe tener exactamente 8 dígitos'
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dni = models.CharField(max_length=8, unique=True, validators=[dni_validator])
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='vendedor')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendedores'
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - DNI: {self.dni}"


class Marca(models.Model):
    """Modelo para marcas de vehículos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'marcas'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
    
    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    """Modelo para modelos de vehículos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='modelos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'modelos'
        verbose_name = 'Modelo'
        verbose_name_plural = 'Modelos'
        unique_together = [['nombre', 'marca']]
    
    def __str__(self):
        return f"{self.marca.nombre} {self.nombre}"


class Oferta(models.Model):
    """Modelo para ofertas de productos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    descuento = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))]
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ofertas'
        verbose_name = 'Oferta'
        verbose_name_plural = 'Ofertas'
    
    def __str__(self):
        return f"Oferta {self.descuento}% ({self.fecha_inicio.date()} - {self.fecha_fin.date()})"
    
    def esta_vigente(self):
        """Verifica si la oferta está vigente"""
        now = timezone.now()
        return self.fecha_inicio <= now <= self.fecha_fin


class Vehiculo(models.Model):
    """Modelo para vehículos"""
    
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('RESERVADO', 'Reservado'),
        ('VENDIDO', 'Vendido'),
        ('DESHABILITADO', 'Deshabilitado'),
    ]
    
    chasis_validator = RegexValidator(
        regex=r'^[A-HJ-NPR-Z0-9]{17}$',
        message='El número de chasis debe tener exactamente 17 caracteres'
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nro_chasis = models.CharField(
        max_length=17, 
        unique=True, 
        validators=[chasis_validator],
        help_text='Número VIN de 17 caracteres'
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    descripcion = models.TextField(blank=True, null=True)
    anio = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )
    imagen = models.URLField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE')
    eliminado = models.BooleanField(default=False)
    modelo = models.ForeignKey(Modelo, on_delete=models.PROTECT, related_name='vehiculos')
    oferta = models.ForeignKey(Oferta, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehiculos'
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
    
    def __str__(self):
        return f"{self.modelo} {self.anio} - {self.nro_chasis}"
    
    def get_precio_con_oferta(self):
        """Calcula el precio con descuento si hay oferta vigente"""
        if self.oferta and self.oferta.esta_vigente():
            descuento = self.precio * (self.oferta.descuento / 100)
            return self.precio - descuento
        return self.precio


class Accesorio(models.Model):
    """Modelo para accesorios de vehículos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    descripcion = models.TextField(blank=True, null=True)
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)
    oferta = models.ForeignKey(Oferta, on_delete=models.SET_NULL, null=True, blank=True, related_name='accesorios')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accesorios'
        verbose_name = 'Accesorio'
        verbose_name_plural = 'Accesorios'
    
    def __str__(self):
        return self.nombre
    
    def get_precio_para_modelo(self, modelo_id):
        """Obtiene el precio del accesorio para un modelo específico"""
        try:
            modelo_accesorio = ModeloAccesorio.objects.get(modelo_id=modelo_id, accesorio=self)
            if self.oferta and self.oferta.esta_vigente():
                descuento = modelo_accesorio.precio * (self.oferta.descuento / 100)
                return modelo_accesorio.precio - descuento
            return modelo_accesorio.precio
        except ModeloAccesorio.DoesNotExist:
            return Decimal('0.00')


class ModeloAccesorio(models.Model):
    """Tabla intermedia para relación Modelo-Accesorio con precio"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE)
    accesorio = models.ForeignKey(Accesorio, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'modelo_accesorios'
        verbose_name = 'Modelo-Accesorio'
        verbose_name_plural = 'Modelos-Accesorios'
        unique_together = [['modelo', 'accesorio']]
    
    def __str__(self):
        return f"{self.modelo} - {self.accesorio}: ${self.precio}"


class Cotizacion(models.Model):
    """Modelo para cotizaciones"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_hora_generada = models.DateTimeField(auto_now_add=True)
    importe_final = models.DecimalField(max_digits=12, decimal_places=2)
    valida = models.BooleanField(default=True)
    fecha_hora_vencimiento = models.DateTimeField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cotizaciones'
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
    
    def __str__(self):
        return f"Cotización {self.id} - Cliente: {self.cliente.nombre}"
    
    def esta_vigente(self):
        """Verifica si la cotización está vigente"""
        return self.valida and timezone.now() <= self.fecha_hora_vencimiento


class CotizacionVehiculo(models.Model):
    """Relación entre cotización y vehículos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='vehiculos')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cotizacion_vehiculos'
        verbose_name = 'Cotización-Vehículo'
        verbose_name_plural = 'Cotizaciones-Vehículos'
        unique_together = [['cotizacion', 'vehiculo']]
    
    def __str__(self):
        return f"{self.cotizacion.id} - {self.vehiculo}"


class CotizacionAccesorio(models.Model):
    """Relación entre cotización vehículo y accesorios"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='accesorios')
    cotizacion_vehiculo = models.ForeignKey(CotizacionVehiculo, on_delete=models.CASCADE, related_name='accesorios')
    accesorio = models.ForeignKey(Accesorio, on_delete=models.PROTECT)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cotizacion_accesorios'
        verbose_name = 'Cotización-Accesorio'
        verbose_name_plural = 'Cotizaciones-Accesorios'
    
    def __str__(self):
        return f"{self.cotizacion.id} - {self.accesorio}"


class Pago(models.Model):
    """Modelo para pagos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nro_pago = models.CharField(max_length=100, unique=True)  # Número del sistema externo
    fecha_hora_generado = models.DateTimeField(auto_now_add=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
    
    def __str__(self):
        return f"Pago {self.nro_pago} - ${self.importe}"


class Reserva(models.Model):
    """Modelo para reservas"""
    
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nro_reserva = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    fecha_hora_generada = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVA')
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_hora_vencimiento = models.DateTimeField()
    cotizacion = models.OneToOneField(Cotizacion, on_delete=models.CASCADE, related_name='reserva')
    pago = models.OneToOneField(Pago, on_delete=models.PROTECT, related_name='reserva')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
    
    def __str__(self):
        return f"Reserva {self.nro_reserva} - Estado: {self.estado}"
    
    def esta_vigente(self):
        """Verifica si la reserva está vigente"""
        return self.estado == 'ACTIVA' and timezone.now() <= self.fecha_hora_vencimiento


class Venta(models.Model):
    """Modelo para ventas"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nro_venta = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    fecha_hora_generada = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    concretada = models.BooleanField(default=False)
    comision = models.DecimalField(max_digits=10, decimal_places=2)
    pago = models.OneToOneField(Pago, on_delete=models.PROTECT, related_name='venta')
    cotizacion = models.OneToOneField(Cotizacion, on_delete=models.CASCADE, related_name='venta')
    vendedor = models.ForeignKey(Vendedor, on_delete=models.PROTECT, related_name='ventas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ventas'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
    
    def __str__(self):
        return f"Venta {self.nro_venta} - Vendedor: {self.vendedor.nombre}"
