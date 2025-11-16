from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegistroClienteView, LoginView, VehiculoViewSet, AccesorioViewSet,
    CotizacionViewSet, ReservaViewSet, VentaViewSet, PagoView
)

router = DefaultRouter()
router.register(r'vehiculos', VehiculoViewSet)
router.register(r'accesorios', AccesorioViewSet)
router.register(r'cotizaciones', CotizacionViewSet, basename='cotizacion')
router.register(r'reservas', ReservaViewSet, basename='reserva')
router.register(r'ventas', VentaViewSet, basename='venta')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/registro/', RegistroClienteView.as_view(), name='registro'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('pagos/realizar/', PagoView.as_view(), name='realizar-pago'),
]
