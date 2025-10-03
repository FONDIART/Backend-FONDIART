from django.urls import path
from .views import TokenizeArtworkView, GetContractAddressView

urlpatterns = [
    path('tokenize/', TokenizeArtworkView.as_view(), name='tokenize-artwork'),
    path('artwork/<int:artwork_id>/contract/', GetContractAddressView.as_view(), name='get_contract_address'),
]
