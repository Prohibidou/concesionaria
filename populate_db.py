import os
import django
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flycar_project.settings')
django.setup()

from core.models import Marca, Modelo, Vehiculo, Accesorio, ModeloAccesorio, Oferta
from django.utils import timezone

def populate_db():
    print("Creando datos de prueba...")
    
    # Marcas
    toyota, _ = Marca.objects.get_or_create(nombre='Toyota')
    ford, _ = Marca.objects.get_or_create(nombre='Ford')
    chevrolet, _ = Marca.objects.get_or_create(nombre='Chevrolet')
    
    # Modelos
    corolla, _ = Modelo.objects.get_or_create(nombre='Corolla', marca=toyota)
    hilux, _ = Modelo.objects.get_or_create(nombre='Hilux', marca=toyota)
    ranger, _ = Modelo.objects.get_or_create(nombre='Ranger', marca=ford)
    cruze, _ = Modelo.objects.get_or_create(nombre='Cruze', marca=chevrolet)
    
    # Accesorios
    acc_polarizado, _ = Accesorio.objects.get_or_create(nombre='Polarizado', stock=100, descripcion='Polarizado intermedio')
    acc_alarma, _ = Accesorio.objects.get_or_create(nombre='Alarma Volumétrica', stock=50)
    acc_tuercas, _ = Accesorio.objects.get_or_create(nombre='Tuercas de Seguridad', stock=200)
    
    # Precios de accesorios por modelo
    for modelo in [corolla, hilux, ranger, cruze]:
        ModeloAccesorio.objects.get_or_create(modelo=modelo, accesorio=acc_polarizado, defaults={'precio': Decimal('15000')})
        ModeloAccesorio.objects.get_or_create(modelo=modelo, accesorio=acc_alarma, defaults={'precio': Decimal('45000')})
        ModeloAccesorio.objects.get_or_create(modelo=modelo, accesorio=acc_tuercas, defaults={'precio': Decimal('8000')})

    # Vehículos
    estados = ['DISPONIBLE', 'DISPONIBLE', 'DISPONIBLE', 'RESERVADO']
    
    for i in range(10):
        modelo = random.choice([corolla, hilux, ranger, cruze])
        anio = random.choice([2023, 2024, 2025])
        precio_base = Decimal('20000000') if modelo in [corolla, cruze] else Decimal('35000000')
        precio = precio_base + Decimal(random.randint(0, 5000000))
        
        chasis = f"VIN{modelo.nombre[:3].upper()}{random.randint(1000000000, 9999999999)}"
        
        if not Vehiculo.objects.filter(nro_chasis=chasis).exists():
            Vehiculo.objects.create(
                nro_chasis=chasis,
                precio=precio,
                descripcion=f"{modelo.marca.nombre} {modelo.nombre} {anio} Full",
                anio=anio,
                modelo=modelo,
                estado=random.choice(estados)
            )
            print(f"Vehículo creado: {modelo.nombre} {anio}")

    print("¡Datos de prueba creados exitosamente!")

if __name__ == '__main__':
    populate_db()
