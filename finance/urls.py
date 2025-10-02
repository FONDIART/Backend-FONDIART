from django.urls import path
from .views import (
    CreateTransaccionView, 
    CuentaComitenteDetailView, 
    CuentaComitenteCreateView,
    CuentaComitenteUpdateView
)

urlpatterns = [
    path('transacciones/', CreateTransaccionView.as_view(), name='create-transaccion'),
    path('cuenta/', CuentaComitenteDetailView.as_view(), name='cuenta-comitente-detail'),
    path('cuenta/crear/', CuentaComitenteCreateView.as_view(), name='cuenta-comitente-create'),
    path('cuenta/actualizar/<int:user__id>/', CuentaComitenteUpdateView.as_view(), name='cuenta-comitente-update'),
]