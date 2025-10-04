from django.urls import path
from .views import (
    CreateTransaccionView, 
    CuentaComitenteDetailView, 
    CuentaComitenteCreateView,
    CuentaComitenteUpdateView,
    BuyTokensView,
    UserTokenHoldingsView,
    DonationView,
    FundProjectView
)

urlpatterns = [
    path('transacciones/', CreateTransaccionView.as_view(), name='create-transaccion'),
    path('cuenta/', CuentaComitenteDetailView.as_view(), name='cuenta-comitente-detail'),
    path('cuenta/crear/', CuentaComitenteCreateView.as_view(), name='cuenta-comitente-create'),
    path('cuenta/actualizar/<int:user__id>/', CuentaComitenteUpdateView.as_view(), name='cuenta-comitente-update'),
    path('tokens/buy/', BuyTokensView.as_view(), name='buy-tokens'),
    path('users/<int:user_id>/tokens/', UserTokenHoldingsView.as_view(), name='user-token-holdings'),
    path('donations/', DonationView.as_view(), name='create-donation'),
    path('projects/fund/', FundProjectView.as_view(), name='fund-project'),
]
