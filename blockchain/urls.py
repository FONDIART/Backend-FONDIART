from django.urls import path
from .views import (
    CreateCuadroView, 
    ContractInfoView, 
    DistribuirTokensView, 
    CertificarPropiedadView, 
    BalanceView
)

urlpatterns = [
    path('cuadros/create/', CreateCuadroView.as_view(), name='create-cuadro'),
    path('contract/info/', ContractInfoView.as_view(), name='contract-info'),
    path('contract/distribuir/', DistribuirTokensView.as_view(), name='distribuir-tokens'),
    path('contract/certificar/', CertificarPropiedadView.as_view(), name='certificar-propiedad'),
    path('contract/balance/', BalanceView.as_view(), name='contract-balance'),
]