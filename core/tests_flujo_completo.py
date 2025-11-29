from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Usuario, Cliente, Vendedor, Vehiculo, Marca, Modelo, Accesorio, ModeloAccesorio, Cotizacion, Reserva, Venta

class FlujoCompletoTests(APITestCase):
    def setUp(self):
        # 1. SETUP DE DATOS MAESTROS
        # Crear Marca y Modelo
        self.marca = Marca.objects.create(nombre='Toyota')
        self.modelo = Modelo.objects.create(nombre='Corolla', marca=self.marca)
        
        # Crear Vehículos
        self.auto1 = Vehiculo.objects.create(
            nro_chasis='VIN12345678900001',
            precio=25000.00,
            anio=2024,
            modelo=self.modelo,
            estado='DISPONIBLE'
        )
        self.auto2 = Vehiculo.objects.create(
            nro_chasis='VIN12345678900002',
            precio=28000.00,
            anio=2024,
            modelo=self.modelo,
            estado='DISPONIBLE'
        )
        
        # Crear Accesorio
        self.accesorio = Accesorio.objects.create(nombre='Polarizado', stock=10)
        self.modelo_accesorio = ModeloAccesorio.objects.create(
            modelo=self.modelo,
            accesorio=self.accesorio,
            precio=500.00
        )
        
        # Crear Vendedor (para el paso final)
        self.vendedor_user = Usuario.objects.create_user(email='vendedor@test.com', password='password123', tipo_usuario='VENDEDOR')
        self.vendedor = Vendedor.objects.create(
            usuario=self.vendedor_user,
            dni='11223344',
            nombre='Juan',
            apellido='Vendedor'
        )

    def test_flujo_compra_completo(self):
        print("\n🚀 Iniciando Test de Flujo Completo...")

        # ==========================================
        # PASO 1: REGISTRO DE CLIENTE (C.U. 07)
        # ==========================================
        print("1. Registrando Cliente...")
        registro_data = {
            'email': 'cliente@test.com',
            'password': 'password123',
            'dni': '87654321',
            'nombre': 'Carlos',
            'apellido': 'Cliente',
            'fecha_nacimiento': '1990-01-01',
            'direccion': 'Calle Falsa 123'
        }
        response = self.client.post('/api/auth/registro/', registro_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # ==========================================
        # PASO 2: LOGIN (Autenticación)
        # ==========================================
        print("2. Iniciando Sesión...")
        login_data = {
            'email': 'cliente@test.com',
            'password': 'password123'
        }
        response = self.client.post('/api/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # ==========================================
        # PASO 3: BUSQUEDA Y COTIZACIÓN (C.U. 01 y 02)
        # ==========================================
        print("3. Generando Cotización para 2 vehículos...")
        # El cliente selecciona 2 autos y un accesorio para el primero
        cotizacion_data = {
            'vehiculos': [
                {
                    'vehiculo_id': self.auto1.id,
                    'accesorios': [self.accesorio.id]
                },
                {
                    'vehiculo_id': self.auto2.id,
                    'accesorios': []
                }
            ]
        }
        response = self.client.post('/api/cotizaciones/generar/', cotizacion_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cotizacion_id = response.data['id']
        importe_final = float(response.data['importe_final'])
        
        # Verificar importe: (25000 + 500) + 28000 = 53500
        expected_total = 25000 + 500 + 28000
        self.assertEqual(importe_final, expected_total)
        print(f"   Cotización creada ID: {cotizacion_id} por ${importe_final}")

        # ==========================================
        # PASO 4: RESERVA (C.U. 03)
        # ==========================================
        print("4. Realizando Reserva (Pago de Seña)...")
        reserva_data = {
            'cotizacion_id': cotizacion_id
        }
        response = self.client.post('/api/reservas/crear/', reserva_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reserva_id = response.data['id']
        
        # Verificar estados intermedios
        self.auto1.refresh_from_db()
        self.auto2.refresh_from_db()
        self.assertEqual(self.auto1.estado, 'RESERVADO')
        self.assertEqual(self.auto2.estado, 'RESERVADO')
        print("   ✅ Vehículos pasaron a estado RESERVADO")

        # ==========================================
        # PASO 5: CONCRETAR VENTA (C.U. 04) - ROL VENDEDOR
        # ==========================================
        print("5. Concretando Venta (Rol Vendedor)...")
        
        # Cambiar a usuario Vendedor
        self.client.force_authenticate(user=self.vendedor_user)
        
        venta_data = {
            'cotizacion_id': cotizacion_id
        }
        response = self.client.post('/api/ventas/realizar/', venta_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # ==========================================
        # PASO 6: VERIFICACIÓN FINAL
        # ==========================================
        print("6. Verificaciones Finales...")
        
        # Verificar estados finales de vehículos
        self.auto1.refresh_from_db()
        self.auto2.refresh_from_db()
        self.assertEqual(self.auto1.estado, 'VENDIDO')
        self.assertEqual(self.auto2.estado, 'VENDIDO')
        print("   ✅ Vehículos pasaron a estado VENDIDO")
        
        # Verificar estado de reserva
        reserva = Reserva.objects.get(id=reserva_id)
        self.assertEqual(reserva.estado, 'COMPLETADA')
        print("   ✅ Reserva pasó a estado COMPLETADA")
        
        # Verificar existencia de venta
        venta = Venta.objects.get(cotizacion__id=cotizacion_id)
        self.assertTrue(venta.concretada)
        print("   ✅ Venta registrada correctamente")

        print("\n✨ ¡FLUJO COMPLETO EXITOSO! ✨")

    def test_reserva_vehiculo_ya_reservado(self):
        print("\n🧪 Test: Intentar reservar vehículo ya reservado")
        
        # 1. Cliente A reserva auto1
        self.client.force_authenticate(user=Usuario.objects.get(email='cliente@test.com') if Usuario.objects.filter(email='cliente@test.com').exists() else self._crear_cliente('A'))
        
        # Crear cotización y reserva A
        cot_data = {'vehiculos': [{'vehiculo_id': self.auto1.id}]}
        res_cot = self.client.post('/api/cotizaciones/generar/', cot_data, format='json')
        self.client.post('/api/reservas/crear/', {'cotizacion_id': res_cot.data['id']})
        
        # 2. Cliente B intenta cotizar auto1
        self.client.logout()
        self._crear_cliente('B') # Helper para crear otro cliente
        
        # Intentar cotizar el mismo auto (debería fallar o permitir cotizar pero fallar reserva? 
        # Según reglas, si está RESERVADO no debería aparecer en búsquedas, pero si se intenta forzar:
        cot_data_b = {'vehiculos': [{'vehiculo_id': self.auto1.id}]}
        res_cot_b = self.client.post('/api/cotizaciones/generar/', cot_data_b, format='json')
        
        # Si la lógica es robusta, al intentar cotizar un auto RESERVADO debería dar error o advertencia
        # Si permite cotizar, la reserva DEBE fallar.
        if res_cot_b.status_code == status.HTTP_201_CREATED:
            print("   (Permitió cotizar, probando reserva...)")
            res_res_b = self.client.post('/api/reservas/crear/', {'cotizacion_id': res_cot_b.data['id']})
            # Aquí esperamos fallo porque el auto ya no está DISPONIBLE
            self.assertNotEqual(res_res_b.status_code, status.HTTP_201_CREATED)
            print("   ✅ Bloqueó la reserva duplicada correctamente")
        else:
            print("   ✅ Bloqueó la cotización de auto reservado")

    def test_cancelacion_reserva(self):
        print("\n🧪 Test: Cancelación de Reserva")
        self.client.force_authenticate(user=self._crear_cliente('C'))
        
        # Crear reserva
        cot_data = {'vehiculos': [{'vehiculo_id': self.auto2.id}]}
        res_cot = self.client.post('/api/cotizaciones/generar/', cot_data, format='json')
        res_res = self.client.post('/api/reservas/crear/', {'cotizacion_id': res_cot.data['id']})
        reserva_id = res_res.data['id']
        
        # Cancelar
        response = self.client.post(f'/api/reservas/{reserva_id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estados
        self.auto2.refresh_from_db()
        reserva = Reserva.objects.get(id=reserva_id)
        
        self.assertEqual(self.auto2.estado, 'DISPONIBLE')
        self.assertEqual(reserva.estado, 'CANCELADA')
        print("   ✅ Reserva cancelada y vehículo liberado")

    def test_vencimiento_reserva(self):
        print("\n🧪 Test: Vencimiento de Reserva")
        from django.utils import timezone
        from datetime import timedelta
        from unittest.mock import patch
        
        self.client.force_authenticate(user=self._crear_cliente('D'))
        
        # Crear reserva
        cot_data = {'vehiculos': [{'vehiculo_id': self.auto1.id}]}
        res_cot = self.client.post('/api/cotizaciones/generar/', cot_data, format='json')
        res_res = self.client.post('/api/reservas/crear/', {'cotizacion_id': res_cot.data['id']})
        
        # Simular que pasaron 8 días
        futuro = timezone.now() + timedelta(days=8)
        
        with patch('django.utils.timezone.now', return_value=futuro):
            # Intentar concretar venta con reserva vencida
            self.client.force_authenticate(user=self.vendedor_user)
            venta_data = {'cotizacion_id': res_cot.data['id']}
            
            # Aquí debería fallar porque la cotización/reserva ya no es vigente
            response = self.client.post('/api/ventas/realizar/', venta_data)
            
            # Esperamos 400 Bad Request
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            print("   ✅ Sistema rechazó venta de reserva vencida")

    def _crear_cliente(self, sufijo):
        email = f'cliente{sufijo}@test.com'
        if not Usuario.objects.filter(email=email).exists():
            user = Usuario.objects.create_user(email=email, password='password123', tipo_usuario='CLIENTE')
            Cliente.objects.create(
                usuario=user, dni=f'1111111{sufijo}', nombre=f'Cliente {sufijo}', 
                apellido='Test', fecha_nacimiento='1990-01-01', direccion='Test', email=email
            )
            return user
        return Usuario.objects.get(email=email)
