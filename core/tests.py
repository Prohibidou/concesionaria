from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Usuario, Cliente, Vendedor, Marca, Modelo, Vehiculo, 
    Accesorio, ModeloAccesorio, Cotizacion, Reserva, Pago, Venta
)

class TestCasosDeUso(APITestCase):
    
    def setUp(self):
        # Cliente
        self.cliente_user = Usuario.objects.create_user(
            email='cliente@test.com', 
            password='password123',
            tipo_usuario='CLIENTE'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            dni='12345678',
            nombre='Juan',
            apellido='Perez',
            fecha_nacimiento='1990-01-01',
            direccion='Calle Falsa 123',
            email='cliente@test.com'
        )
        
        # Vendedor
        self.vendedor_user = Usuario.objects.create_user(
            email='vendedor@test.com', 
            password='password123',
            tipo_usuario='VENDEDOR'
        )
        self.vendedor = Vendedor.objects.create(
            usuario=self.vendedor_user,
            dni='87654321',
            nombre='Ana',
            apellido='Gomez'
        )
        
        # Vehículo
        self.marca = Marca.objects.create(nombre='Toyota')
        self.modelo = Modelo.objects.create(nombre='Corolla', marca=self.marca)
        self.vehiculo = Vehiculo.objects.create(
            nro_chasis='12345678901234567',
            precio=Decimal('25000.00'),
            anio=2023,
            modelo=self.modelo,
            estado='DISPONIBLE'
        )

    def test_cu01_simular_cotizacion(self):
        """C.U. 01 - Simular Cotización"""
        url = reverse('cotizacion-simular')
        # Estructura actualizada según ItemCotizacionSerializer
        data = {
            'vehiculos': [
                {'vehiculo_id': str(self.vehiculo.id), 'accesorios': []}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['importe_total']), self.vehiculo.precio)
        self.assertEqual(len(response.data['detalle']), 1)

    def test_cu02_generar_cotizacion(self):
        """C.U. 02 - Generar Cotización"""
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('cotizacion-generar')
        data = {
            'vehiculos': [
                {'vehiculo_id': str(self.vehiculo.id), 'accesorios': []}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cotizacion.objects.count(), 1)
        cotizacion = Cotizacion.objects.first()
        self.assertEqual(cotizacion.cliente, self.cliente)
        self.assertEqual(cotizacion.importe_final, self.vehiculo.precio)

    def test_cu03_realizar_reserva(self):
        """C.U. 03 - Realizar Reserva"""
        # Primero generar cotización
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            importe_final=self.vehiculo.precio,
            fecha_hora_vencimiento=timezone.now() + timedelta(hours=48)
        )
        # Asociar vehículo
        from core.models import CotizacionVehiculo
        CotizacionVehiculo.objects.create(
            cotizacion=cotizacion,
            vehiculo=self.vehiculo,
            precio_unitario=self.vehiculo.precio
        )
        
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('reserva-crear')
        data = {'cotizacion_id': str(cotizacion.id)}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reserva.objects.count(), 1)
        reserva = Reserva.objects.first()
        self.assertEqual(reserva.cotizacion, cotizacion)
        self.assertEqual(reserva.estado, 'ACTIVA')
        
        # Verificar cambio de estado del vehículo
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.estado, 'RESERVADO')

    def test_cu04_realizar_venta(self):
        """C.U. 04 - Realizar Venta"""
        # Setup: Cotización y Reserva previa
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            importe_final=self.vehiculo.precio,
            fecha_hora_vencimiento=timezone.now() + timedelta(days=7)
        )
        from core.models import CotizacionVehiculo
        CotizacionVehiculo.objects.create(
            cotizacion=cotizacion,
            vehiculo=self.vehiculo,
            precio_unitario=self.vehiculo.precio
        )
        
        # Reserva y pago de seña
        pago_seña = Pago.objects.create(nro_pago='SENA-123', importe=self.vehiculo.precio * Decimal('0.05'))
        reserva = Reserva.objects.create(
            cotizacion=cotizacion,
            pago=pago_seña,
            importe=pago_seña.importe,
            fecha_hora_vencimiento=timezone.now() + timedelta(days=7),
            estado='ACTIVA'
        )
        self.vehiculo.estado = 'RESERVADO'
        self.vehiculo.save()

        # Acción: Vendedor realiza la venta
        self.client.force_authenticate(user=self.vendedor_user)
        url = reverse('venta-realizar')
        data = {'cotizacion_id': str(cotizacion.id)}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificaciones
        self.assertEqual(Venta.objects.count(), 1)
        venta = Venta.objects.first()
        self.assertEqual(venta.vendedor, self.vendedor)
        self.assertTrue(venta.concretada)
        
        # Vehículo debe estar VENDIDO
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.estado, 'VENDIDO')
        
        # Reserva debe estar COMPLETADA
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'COMPLETADA')

    def test_cu05_realizar_pago(self):
        """C.U. 05 - Realizar Pago"""
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('realizar-pago')
        data = {
            'importe': '1000.00',
            'metodo_pago': 'TARJETA'
        }
        
        response = self.client.post(url, data, format='json')
        
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('nro_pago', response.data)
            self.assertTrue(response.data['success'])
        elif response.status_code == status.HTTP_402_PAYMENT_REQUIRED:
            self.assertFalse(response.data['success'])

    def test_cu06_cancelar_reserva(self):
        """C.U. 06 - Cancelar Reserva"""
        # Setup
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            importe_final=self.vehiculo.precio,
            fecha_hora_vencimiento=timezone.now() + timedelta(days=7)
        )
        from core.models import CotizacionVehiculo
        CotizacionVehiculo.objects.create(
            cotizacion=cotizacion,
            vehiculo=self.vehiculo,
            precio_unitario=self.vehiculo.precio
        )
        pago = Pago.objects.create(nro_pago='TEST-PAY', importe=1000)
        reserva = Reserva.objects.create(
            cotizacion=cotizacion,
            pago=pago,
            importe=1000,
            fecha_hora_vencimiento=timezone.now() + timedelta(days=7),
            estado='ACTIVA'
        )
        self.vehiculo.estado = 'RESERVADO'
        self.vehiculo.save()
        
        self.client.force_authenticate(user=self.vendedor_user)
        url = reverse('reserva-cancelar', args=[reserva.id])
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'CANCELADA')
        
        self.vehiculo.refresh_from_db()
        self.assertEqual(self.vehiculo.estado, 'DISPONIBLE')

    def test_cu07_buscar_cotizaciones(self):
        """C.U. 07 - Buscar/Ver Cotizaciones"""
        # Crear 2 cotizaciones para el cliente
        for _ in range(2):
            Cotizacion.objects.create(
                cliente=self.cliente,
                importe_final=Decimal('100.00'),
                fecha_hora_vencimiento=timezone.now() + timedelta(days=1)
            )
            
        self.client.force_authenticate(user=self.cliente_user)
        url = reverse('cotizacion-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ajuste por paginación: response.data['results'] o response.data
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 2)

    def test_cu13_gestion_cuenta(self):
        """C.U. 13 - Gestión de Cuenta (Login)"""
        url = reverse('login')
        data = {
            'email': 'cliente@test.com',
            'password': 'password123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_registro_cliente(self):
        """Test Registro de Nuevo Cliente"""
        url = reverse('registro')
        data = {
            'email': 'nuevo@cliente.com',
            'password': 'password123',
            'nombre': 'Nuevo',
            'apellido': 'Cliente',
            'dni': '11223344',
            'fecha_nacimiento': '2000-01-01',
            'direccion': 'Calle Nueva 123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.filter(email='nuevo@cliente.com').exists())
        self.assertTrue(Cliente.objects.filter(dni='11223344').exists())
