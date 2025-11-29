from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from decimal import Decimal
from datetime import timedelta
import uuid

from .models import (
    Usuario, Cliente, Vendedor, Vehiculo, Accesorio, Cotizacion,
    CotizacionVehiculo, CotizacionAccesorio, Reserva, Venta, Pago,
    ModeloAccesorio, Oferta
)
from .serializers import (
    UsuarioSerializer, RegistroClienteSerializer, LoginSerializer,
    VehiculoSerializer, AccesorioSerializer, CotizacionSerializer,
    SimularCotizacionSerializer, GenerarCotizacionSerializer,
    ReservaSerializer, VentaSerializer, PagoSerializer, RealizarPagoSerializer
)

# ==================== AUTHENTICATION ====================

class RegistroClienteView(generics.CreateAPIView):
    serializer_class = RegistroClienteSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'tipo_usuario': user.tipo_usuario,
            'email': user.email
        })

# ==================== PRODUCTOS ====================

class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.filter(eliminado=False)
    serializer_class = VehiculoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

class AccesorioViewSet(viewsets.ModelViewSet):
    queryset = Accesorio.objects.filter(eliminado=False)
    serializer_class = AccesorioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# ==================== COTIZACIONES ====================

class CotizacionViewSet(viewsets.ModelViewSet):
    serializer_class = CotizacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'CLIENTE':
            return Cotizacion.objects.filter(cliente__usuario=user)
        elif user.tipo_usuario == 'VENDEDOR':
            return Cotizacion.objects.all() # Vendedores ven todas
        return Cotizacion.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def simular(self, request):
        """C.U. 01 - Simular Cotización"""
        serializer = SimularCotizacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        vehiculos_data = data['vehiculos']
        
        total = Decimal('0.00')
        detalle = []
        
        for v_data in vehiculos_data:
            vehiculo = get_object_or_404(Vehiculo, id=v_data['vehiculo_id'])
            precio_vehiculo = vehiculo.get_precio_con_oferta()
            total += precio_vehiculo
            
            accesorios_detalle = []
            if 'accesorios' in v_data:
                for acc_id in v_data['accesorios']:
                    accesorio = get_object_or_404(Accesorio, id=acc_id)
                    precio_acc = accesorio.get_precio_para_modelo(vehiculo.modelo.id)
                    total += precio_acc
                    accesorios_detalle.append({
                        'id': accesorio.id,
                        'nombre': accesorio.nombre,
                        'precio': precio_acc
                    })
            
            detalle.append({
                'vehiculo': {
                    'id': vehiculo.id,
                    'modelo': str(vehiculo.modelo),
                    'precio': precio_vehiculo
                },
                'accesorios': accesorios_detalle
            })
            
        return Response({
            'importe_total': total,
            'detalle': detalle
        })

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def generar(self, request):
        """C.U. 02 - Generar Cotización"""
        serializer = GenerarCotizacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        user = request.user
        
        # Determinar cliente
        if user.tipo_usuario == 'CLIENTE':
            cliente = user.cliente
            # Invalidar cotización anterior vigente, EXCEPTO si tiene reserva activa
            Cotizacion.objects.filter(
                cliente=cliente, 
                valida=True
            ).exclude(
                reserva__estado='ACTIVA'
            ).update(valida=False)
        elif user.tipo_usuario == 'VENDEDOR':
            cliente_id = data.get('cliente_id')
            cliente = get_object_or_404(Cliente, id=cliente_id)
        else:
            return Response({'error': 'Rol no autorizado'}, status=status.HTTP_403_FORBIDDEN)
            
        # Crear cotización
        cotizacion = Cotizacion.objects.create(
            cliente=cliente,
            importe_final=0, # Se calcula después
            fecha_hora_vencimiento=timezone.now() + timedelta(hours=48)
        )
        
        total = Decimal('0.00')
        
        # Procesar vehículos y accesorios
        for v_data in data['vehiculos']:
            vehiculo = get_object_or_404(Vehiculo, id=v_data['vehiculo_id'])
            
            # Reservar vehículo temporalmente (lógica simplificada)
            # En realidad el estado cambia a RESERVADO solo con la Reserva (C.U. 3)
            # Pero aquí ya se asocia a la cotización
            
            precio_vehiculo = vehiculo.get_precio_con_oferta()
            total += precio_vehiculo
            
            cot_vehiculo = CotizacionVehiculo.objects.create(
                cotizacion=cotizacion,
                vehiculo=vehiculo,
                precio_unitario=precio_vehiculo
            )
            
            if 'accesorios' in v_data:
                for acc_id in v_data['accesorios']:
                    accesorio = get_object_or_404(Accesorio, id=acc_id)
                    precio_acc = accesorio.get_precio_para_modelo(vehiculo.modelo.id)
                    total += precio_acc
                    
                    CotizacionAccesorio.objects.create(
                        cotizacion=cotizacion,
                        cotizacion_vehiculo=cot_vehiculo,
                        accesorio=accesorio,
                        precio_unitario=precio_acc
                    )
        
        cotizacion.importe_final = total
        cotizacion.save()
        
        return Response(CotizacionSerializer(cotizacion).data, status=status.HTTP_201_CREATED)

# ==================== RESERVAS Y PAGOS ====================

class ReservaViewSet(viewsets.ModelViewSet):
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['fecha_hora_generada']
    ordering = ['-fecha_hora_generada']
    
    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'CLIENTE':
            return Reserva.objects.filter(cotizacion__cliente__usuario=user).order_by('-fecha_hora_generada')
        elif user.tipo_usuario == 'VENDEDOR':
            return Reserva.objects.all().order_by('-fecha_hora_generada')
        return Reserva.objects.none()

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def crear(self, request):
        """C.U. 03 - Realizar Reserva"""
        cotizacion_id = request.data.get('cotizacion_id')
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
        
        # Validaciones
        if not cotizacion.esta_vigente():
            return Response({'error': 'Cotización vencida'}, status=status.HTTP_400_BAD_REQUEST)
        
        if hasattr(cotizacion, 'reserva'):
            return Response({'error': 'Cotización ya tiene reserva'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Calcular seña (5%)
        importe_seña = cotizacion.importe_final * Decimal('0.05')
        
        # C.U. 05 - Realizar Pago (Simulado)
        # Aquí llamaríamos al servicio de pago externo
        # Simulamos éxito creando el registro de pago
        pago = Pago.objects.create(
            nro_pago=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            importe=importe_seña
        )
        
        # Crear reserva
        reserva = Reserva.objects.create(
            cotizacion=cotizacion,
            pago=pago,
            importe=importe_seña,
            fecha_hora_vencimiento=timezone.now() + timedelta(days=7)
        )
        
        # Actualizar estado de vehículos a RESERVADO
        for cv in cotizacion.vehiculos.all():
            cv.vehiculo.estado = 'RESERVADO'
            cv.vehiculo.save()
            
        # Extender validez de cotización
        cotizacion.fecha_hora_vencimiento = reserva.fecha_hora_vencimiento
        cotizacion.save()
        
        return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancelar(self, request, pk=None):
        """C.U. 06 - Cancelar Reserva"""
        reserva = self.get_object()
        
        if reserva.estado != 'ACTIVA':
            return Response({'error': 'Reserva no activa'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Devolución de pago (Simulado)
        # ... lógica de devolución ...
        
        reserva.estado = 'CANCELADA'
        reserva.save()
        
        # Liberar vehículos
        for cv in reserva.cotizacion.vehiculos.all():
            cv.vehiculo.estado = 'DISPONIBLE'
            cv.vehiculo.save()
            
        return Response({'status': 'Reserva cancelada y pago devuelto'})

class VentaViewSet(viewsets.ModelViewSet):
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated] # Solo vendedores
    
    def get_queryset(self):
        if self.request.user.tipo_usuario == 'VENDEDOR':
            return Venta.objects.filter(vendedor__usuario=self.request.user)
        return Venta.objects.none()

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def realizar(self, request):
        """C.U. 04 - Realizar Venta"""
        cotizacion_id = request.data.get('cotizacion_id')
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
        vendedor = request.user.vendedor
        
        if not cotizacion.esta_vigente():
            return Response({'error': 'Cotización vencida'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Calcular importe a pagar
        importe_total = cotizacion.importe_final
        if hasattr(cotizacion, 'reserva') and cotizacion.reserva.estado == 'ACTIVA':
            importe_total -= cotizacion.reserva.importe
            cotizacion.reserva.estado = 'COMPLETADA'
            cotizacion.reserva.save()
            
        # C.U. 05 - Realizar Pago
        pago = Pago.objects.create(
            nro_pago=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            importe=importe_total
        )
        
        # Crear venta
        venta = Venta.objects.create(
            cotizacion=cotizacion,
            pago=pago,
            vendedor=vendedor,
            concretada=True,
            comision=cotizacion.importe_final * Decimal('0.10') # 10% comisión
        )
        
        # Marcar vehículos como VENDIDOS
        for cv in cotizacion.vehiculos.all():
            cv.vehiculo.estado = 'VENDIDO'
            cv.vehiculo.save()
            
        return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)

class PagoView(APIView):
    """C.U. 05 - Realizar Pago (Endpoint independiente)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = RealizarPagoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Simular integración con sistema externo
        import random
        if random.random() > 0.1: # 90% éxito
            nro_pago = f"PAY-{uuid.uuid4().hex[:8].upper()}"
            return Response({
                'success': True,
                'nro_pago': nro_pago,
                'mensaje': 'Pago realizado con éxito'
            })
        else:
            return Response({
                'success': False,
                'mensaje': 'Pago rechazado por el sistema externo'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
