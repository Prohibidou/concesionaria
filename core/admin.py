from django.contrib import admin
from .models import (
    Usuario, Cliente, Vendedor, Marca, Modelo, Vehiculo, 
    Accesorio, ModeloAccesorio, Oferta, Cotizacion, 
    CotizacionVehiculo, CotizacionAccesorio, Reserva, Venta, Pago
)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'tipo_usuario', 'is_active', 'is_staff')
    list_filter = ('tipo_usuario', 'is_active')
    search_fields = ('email',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombre', 'apellido', 'email')
    search_fields = ('dni', 'nombre', 'apellido', 'email')

@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombre', 'apellido')
    search_fields = ('dni', 'nombre', 'apellido')

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca')
    list_filter = ('marca',)
    search_fields = ('nombre', 'marca__nombre')

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('nro_chasis', 'modelo', 'anio', 'precio', 'estado')
    list_filter = ('estado', 'anio', 'modelo__marca')
    search_fields = ('nro_chasis', 'modelo__nombre')

@admin.register(Accesorio)
class AccesorioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock', 'habilitado')
    list_filter = ('habilitado',)
    search_fields = ('nombre',)

@admin.register(ModeloAccesorio)
class ModeloAccesorioAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'accesorio', 'precio')
    list_filter = ('modelo__marca',)

@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ('descuento', 'fecha_inicio', 'fecha_fin', 'esta_vigente')
    list_filter = ('fecha_inicio', 'fecha_fin')

class CotizacionVehiculoInline(admin.TabularInline):
    model = CotizacionVehiculo
    extra = 0

class CotizacionAccesorioInline(admin.TabularInline):
    model = CotizacionAccesorio
    extra = 0

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha_hora_generada', 'importe_final', 'valida')
    list_filter = ('valida', 'fecha_hora_generada')
    search_fields = ('cliente__dni', 'cliente__apellido')
    inlines = [CotizacionVehiculoInline, CotizacionAccesorioInline]

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('nro_reserva', 'cotizacion', 'fecha_hora_generada', 'estado', 'importe')
    list_filter = ('estado', 'fecha_hora_generada')
    search_fields = ('nro_reserva',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('nro_venta', 'vendedor', 'fecha_hora_generada', 'concretada')
    list_filter = ('concretada', 'fecha_hora_generada')
    search_fields = ('nro_venta',)

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('nro_pago', 'importe', 'fecha_hora_generado')
    search_fields = ('nro_pago',)
