from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsAdminRoleUser
from rest_framework_simplejwt.tokens import RefreshToken
from eth_account import Account
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.utils import timezone
import cloudinary.uploader
from django.shortcuts import get_object_or_404
import subprocess

from .models import User, Artwork, Order, Favorite, Wallet, BankAccount, Auction
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    AuthResponseSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ArtworkListItemSerializer,
    ArtworkDetailSerializer,
    ArtworkCreateSerializer,
    ArtworkUpdateSerializer,
    RatingSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    FavoriteResponseSerializer,
    ArtworkStatsSerializer,
    WalletSerializer,
    WalletAddressSerializer,
    BankAccountSerializer,
    AuctionCreateSerializer,
    AuctionSerializer,
)

# Auth Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate wallet
        account = Account.create()
        wallet_data = {
            'address': account.address,
            'private_key': account.key.hex()
        }

        # Save wallet to the database
        Wallet.objects.create(
            user=user,
            address=wallet_data['address'],
            private_key=wallet_data['private_key']
        )

        refresh = RefreshToken.for_user(user)
        response_data = {
            'token': str(refresh.access_token),
            'user': user,
            'wallet': wallet_data
        }

        return Response(AuthResponseSerializer(response_data).data, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            print(f"Generated JWT for user {user.email}: {str(refresh.access_token)}")
            response_data = {
                'token': str(refresh.access_token),
                'user': user
            }
            return Response(AuthResponseSerializer(response_data).data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class MeView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

# User Views
class UserWalletAddressView(generics.RetrieveAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletAddressSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'user_id'

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        try:
            # Retrieve the wallet for the specified user ID
            return Wallet.objects.get(user_id=user_id)
        except Wallet.DoesNotExist:
            # You might want to handle this case, e.g., by raising a 404 error
            from django.http import Http404
            raise Http404
            
class ArtistArtworkListView(generics.ListAPIView):
    serializer_class = ArtworkListItemSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Artwork.objects.filter(artist_id=user_id)

class UserUpdateMeView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserUpdateSerializer

    def get_object(self):
        return self.request.user

class ImageUploadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            upload_result = cloudinary.uploader.upload(file)
            return Response({'url': upload_result['secure_url']}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NonDirectSaleArtworkListView(generics.ListAPIView):
    serializer_class = ArtworkListItemSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Artwork.objects.filter(venta_directa=False)

# Artwork Views
class ArtworkListView(generics.ListAPIView):
    queryset = Artwork.objects.filter(venta_directa=False)
    serializer_class = ArtworkListItemSerializer
    permission_classes = (AllowAny,) # Public access

    # Implement filtering and sorting based on OpenAPI parameters
    def get_queryset(self):
        queryset = super().get_queryset()
        # q: Búsqueda por título/autor/tags
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(artist__name__icontains=q) |
                Q(tags__icontains=q) # Assuming tags are stored as JSONField and can be searched this way
            )
        
        # tag: Filtrar por tag
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__contains=[tag]) # For JSONField

        # sort: relevance, newest, price-asc, price-desc, rating-desc
        sort = self.request.query_params.get('sort', None)
        if sort == 'newest':
            queryset = queryset.order_by('-createdAt')
        elif sort == 'price-asc':
            queryset = queryset.order_by('price')
        elif sort == 'price-desc':
            queryset = queryset.order_by('-price')
        elif sort == 'rating-desc':
            queryset = queryset.order_by('-rating_avg')
        # 'relevance' would require a more complex search backend

        return queryset

class ArtworkCreateView(generics.CreateAPIView):
    queryset = Artwork.objects.all()
    serializer_class = ArtworkCreateSerializer
    permission_classes = (IsAuthenticated,) # Only authenticated users can create

    def perform_create(self, serializer):
        # The data transformation logic is now handled in the serializer's create method.
        # We just need to pass the authenticated user as the artist.
        serializer.save(artist=self.request.user)

# Remaining Artwork Views
class ArtworkRecommendedView(generics.ListAPIView):
    queryset = Artwork.objects.filter(status='approved').order_by('-rating_avg') # Simple recommendation for now
    serializer_class = ArtworkListItemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        limit = self.request.query_params.get('limit', 5)
        try:
            limit = int(limit)
        except ValueError:
            limit = 5 # Default if invalid
        return super().get_queryset()[:limit]

class ArtworkDetailUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Artwork.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ArtworkUpdateSerializer
        return ArtworkDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if self.request.method == 'GET':
            return self.queryset.all()
        
        if user.role == 'admin':
            return self.queryset.all()
        
        # Only allow artist to update their own artworks
        return self.queryset.filter(artist=user)

    def perform_update(self, serializer):
        # If status was approved, set it back to pending on update
        if serializer.instance.status == 'approved':
            serializer.instance.status = 'pending'
        serializer.save()

class ArtworkDeleteView(generics.DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk' # pk is the default, but being explicit is fine

    def get_queryset(self):
        # A user can only delete their own artworks
        return Artwork.objects.filter(artist=self.request.user)

class ArtworkRatingView(APIView):
    permission_classes = (AllowAny,) # Rating can be public
    
    def get(self, request, pk):
        try:
            artwork = Artwork.objects.get(id=pk)
            rating_data = {
                'avg': artwork.rating_avg,
                'count': artwork.rating_count,
            }
            if request.user.is_authenticated:
                # Placeholder for 'my' rating if implemented
                rating_data['my'] = 0 
            return Response(RatingSerializer(rating_data).data)
        except Artwork.DoesNotExist:
            return Response({'error': 'Artwork not found'}, status=status.HTTP_404_NOT_FOUND)

class ArtworkRateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        value = request.data.get('value')
        if not value or not (1 <= value <= 5):
            return Response({'error': 'Invalid rating value (1-5)'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            artwork = Artwork.objects.get(id=pk)
            # Simple rating logic: just update avg and count
            # In a real app, you'd store individual ratings and recalculate
            artwork.rating_avg = (artwork.rating_avg * artwork.rating_count + value) / (artwork.rating_count + 1)
            artwork.rating_count += 1
            artwork.save()

            rating_data = {
                'avg': artwork.rating_avg,
                'count': artwork.rating_count,
                'my': value # Assuming the user just rated this value
            }
            return Response(RatingSerializer(rating_data).data)
        except Artwork.DoesNotExist:
            return Response({'error': 'Artwork not found'}, status=status.HTTP_404_NOT_FOUND)

class MyArtworksView(generics.ListAPIView):
    serializer_class = ArtworkDetailSerializer # Use detail serializer for artist's own artworks
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Artwork.objects.filter(artist=self.request.user, status='approved')

class ArtworkStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        try:
            artwork = Artwork.objects.get(id=pk)
            # Only owner or admin can see stats
            if artwork.artist != request.user and not request.user.role == 'admin':
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            # Placeholder for actual stats calculation
            stats = {
                'artworkId': str(artwork.id),
                'soldFractions': artwork.fractionsTotal - artwork.fractionsLeft,
                'fractionsTotal': artwork.fractionsTotal,
                'soldPct': (artwork.fractionsTotal - artwork.fractionsLeft) / artwork.fractionsTotal * 100 if artwork.fractionsTotal > 0 else 0,
                'revenue': (artwork.fractionsTotal - artwork.fractionsLeft) * artwork.price,
                'timeline': [], # Placeholder
                'buyersTop': [], # Placeholder
            }
            return Response(stats) 
        except Artwork.DoesNotExist:
            return Response({'error': 'Artwork not found'}, status=status.HTTP_404_NOT_FOUND)

# Admin Views
class AdminArtworkListView(generics.ListAPIView):
    queryset = Artwork.objects.all() # Admin can see all statuses
    serializer_class = ArtworkListItemSerializer # Or a more detailed admin serializer
    permission_classes = (IsAdminRoleUser,)

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class AdminArtworkStatusUpdateView(generics.UpdateAPIView):
    queryset = Artwork.objects.all()
    serializer_class = ArtworkDetailSerializer # Use detail serializer for response
    permission_classes = (IsAdminRoleUser,)
    lookup_field = 'id'

    def patch(self, request, pk):
        artwork = self.get_object()
        status_new = request.data.get('status')
        reason = request.data.get('reason')

        if status_new not in ['approved', 'rejected']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        artwork.status = status_new
        if status_new == 'approved':
            artwork.approvedAt = timezone.now()
        else:
            artwork.approvedAt = None # Reset if rejected
        
        # Placeholder for moderation details
        # artwork.moderation_by = request.user
        # artwork.moderation_reason = reason

        artwork.save()
        return Response(self.get_serializer(artwork).data)

# Order Views
class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        # Calculate unitPrice and amount based on artwork fractions
        artwork = serializer.validated_data['artwork']
        fractions = serializer.validated_data['fractions']
        unit_price = artwork.price / artwork.fractionsTotal
        amount = unit_price * fractions

        # Update fractionsLeft in Artwork
        if artwork.fractionsLeft < fractions:
            raise serializers.ValidationError("Not enough fractions available.")
        artwork.fractionsLeft -= fractions
        artwork.save()

        serializer.save(buyer=self.request.user, unitPrice=unit_price, amount=amount, status='pending')

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Order.objects.filter(buyer=self.request.user)
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'

    def get_queryset(self):
        # Only allow buyer to see their own orders
        return Order.objects.filter(buyer=self.request.user)

# Favorite Views
class FavoriteCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        try:
            artwork = Artwork.objects.get(id=pk)
            Favorite.objects.create(user=request.user, artwork=artwork)
            return Response({'favorited': True}, status=status.HTTP_200_OK)
        except Artwork.DoesNotExist:
            return Response({'error': 'Artwork not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError: # If already favorited
            return Response({'favorited': True}, status=status.HTTP_200_OK)

class FavoriteDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk):
        try:
            artwork = Artwork.objects.get(id=pk)
            Favorite.objects.filter(user=request.user, artwork=artwork).delete()
            return Response({'favorited': False}, status=status.HTTP_200_OK)
        except Artwork.DoesNotExist:
            return Response({'error': 'Artwork not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e: # If not favorited, just return false
            return Response({'favorited': False}, status=status.HTTP_200_OK)

class MyFavoritesView(generics.ListAPIView):
    serializer_class = ArtworkListItemSerializer # List of favorite artworks
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Return artworks that the user has favorited
        favorite_artworks_ids = Favorite.objects.filter(user=self.request.user).values_list('artwork__id', flat=True)
        return Artwork.objects.filter(id__in=favorite_artworks_ids)

# Wallet Views
class WalletDetailView(generics.RetrieveAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletAddressSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        # Return the wallet of the current user
        return self.request.user.wallet

class BankAccountListCreateView(generics.ListCreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Return the bank accounts of the current user
        return BankAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Return the bank accounts of the current user
        return BankAccount.objects.filter(user=self.request.user)

# Auction Views
from rest_framework.exceptions import ValidationError

# ... (other imports) ...

class AuctionCreateView(generics.CreateAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionCreateSerializer
    permission_classes = [IsAdminRoleUser]

    def perform_create(self, serializer):
        artwork = get_object_or_404(Artwork, pk=self.kwargs.get('pk'))
        
        # Check if an auction already exists for this artwork
        if hasattr(artwork, 'auction'):
            raise ValidationError('An auction for this artwork already exists.')

        artwork.status = 'approved'
        artwork.save()
        serializer.save(artwork=artwork)

class ArtworkTokenizeView(APIView):
    permission_classes = (IsAdminRoleUser,)

    def post(self, request, pk):
        try:
            artwork = Artwork.objects.get(pk=pk)
        except Artwork.DoesNotExist:
            return Response({"error": "Artwork not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get artist and platform addresses
        try:
            artist_wallet = Wallet.objects.get(user=artwork.artist)
            admin_user = User.objects.get(role='admin')
            platform_wallet = Wallet.objects.get(user=admin_user)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found for artist or platform"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Admin user not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate token symbol
        artist_name_parts = artwork.artist.name.split()
        if len(artist_name_parts) > 1:
            symbol = artist_name_parts[-1][0] + artist_name_parts[0][0]
        else:
            symbol = artwork.artist.name[0:2]
        
        artwork_count = Artwork.objects.filter(artist=artwork.artist).count()
        token_symbol = f"{symbol.upper()}{artwork_count}"

        # Prepare and execute deployment script
        command = [
            "node",
            "--network", "sepolia",
            "scripts/deploy_cuadro_token.cjs",
            artwork.title,
            artwork.artist.name,
            str(artwork.createdAt.year),
            artist_wallet.address,
            platform_wallet.address,
            str(artwork.fractionsTotal),
            token_symbol,
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd="/Users/jorgeantoniosegovia/codigo/FondiArt_back/backend-Fondiart"
            )
            contract_address = result.stdout.strip()
            
            # Save contract address to artwork
            artwork.contract_address = contract_address
            artwork.save()

            return Response({"contract_address": contract_address}, status=status.HTTP_200_OK)
        except subprocess.CalledProcessError as e:
            return Response({"error": "Failed to deploy contract", "details": e.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except FileNotFoundError:
            return Response({"error": "Node.js or deployment script not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AuctionListView(generics.ListAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = (AllowAny,)

class AuctionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = (IsAdminRoleUser,)
    lookup_field = 'pk'