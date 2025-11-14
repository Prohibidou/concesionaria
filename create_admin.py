import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flycar_project.settings')
django.setup()

from core.models import Usuario

def create_superuser():
    email = 'admin@flycar.com'
    password = 'admin123'
    
    if not Usuario.objects.filter(email=email).exists():
        print(f"Creando superusuario: {email}")
        Usuario.objects.create_superuser(email=email, password=password)
        print("Superusuario creado exitosamente.")
    else:
        print("El superusuario ya existe.")

if __name__ == '__main__':
    create_superuser()
