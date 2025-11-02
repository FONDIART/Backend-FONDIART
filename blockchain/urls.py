from django.urls import path
from .views import TokenizeArtworkView, GetContractAddressView, TransferTokensView, InitialTokenDistributionView

urlpatterns = [
    path('tokenize/', TokenizeArtworkView.as_view(), name='tokenize-artwork'),
    path('artwork/<int:artwork_id>/contract/', GetContractAddressView.as_view(), name='get_contract_address'),
    path('transfer-tokens/', TransferTokensView.as_view(), name='transfer-tokens'),
    path('artwork/<int:artwork_id>/distribute/', InitialTokenDistributionView.as_view(), name='initial-token-distribution'),
]
