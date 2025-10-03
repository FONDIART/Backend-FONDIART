from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User, Artwork, Order, Favorite, Wallet, BankAccount, Auction, Bid

# Auth Serializers
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'], # Use email as username
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'], # Pass name to create_user
            role=validated_data['role'],
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class AuthResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = serializers.SerializerMethodField()
    wallet = serializers.DictField(read_only=True, required=False)

    def get_user(self, obj):
        return UserSerializer(obj['user']).data

# User Serializers
class UserSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'avatarUrl', 'createdAt', 'dni', 'phone', 'bio', 'cbu']
        read_only_fields = ['id', 'email', 'role']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'avatarUrl', 'dni', 'phone', 'bio', 'cbu']

# Artwork Serializers
class RatingSerializer(serializers.Serializer):
    avg = serializers.FloatField()
    count = serializers.IntegerField()
    my = serializers.IntegerField(required=False)

class ArtworkListItemSerializer(serializers.ModelSerializer):
    artist = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Artwork
        fields = [
            'id', 'title', 'artist', 'status', 'price', 'fractionFrom',
            'fractionsTotal', 'fractionsLeft', 'tags', 'image', 'rating', 'createdAt'
        ]

    def get_artist(self, obj):
        return {'id': str(obj.artist.id), 'name': obj.artist.name}

    def get_rating(self, obj):
        return {'avg': obj.rating_avg, 'count': obj.rating_count, 'my': 0}

class ArtworkDetailSerializer(ArtworkListItemSerializer):
    gallery = serializers.ListField(child=serializers.URLField())
    description = serializers.CharField()
    ownerId = serializers.CharField(source='artist.id')
    approvedAt = serializers.DateTimeField(allow_null=True)

    class Meta(ArtworkListItemSerializer.Meta):
        fields = ArtworkListItemSerializer.Meta.fields + ['description', 'ownerId', 'gallery', 'approvedAt', 'contract_address']

class ArtworkCreateSerializer(serializers.ModelSerializer):
    image = serializers.URLField(required=True)

    class Meta:
        model = Artwork
        fields = [
            'title', 'description', 'price', 'fractionFrom', 'fractionsTotal',
            'image', 'gallery', 'tags', 'status', 'fractionsLeft',
            'venta_directa', 'estado_venta'
        ]
        read_only_fields = ['status']
        extra_kwargs = {
            'title': {'required': True},
            'description': {'required': True},
            'tags': {'required': True},
            'price': {'required': False},
            'fractionFrom': {'required': False},
            'fractionsTotal': {'required': False},
            'fractionsLeft': {'required': False},
            'venta_directa': {'required': False},
            'estado_venta': {'required': False},
        }

    def validate(self, attrs):
        missing = []
        for f in ['title', 'description', 'tags', 'image']:
            if not attrs.get(f):
                missing.append(f)
        if missing:
            raise ValidationError({f: 'Este campo es obligatorio.' for f in missing})

        if attrs.get('venta_directa') is True and attrs.get('price') in (None, ''):
            raise ValidationError({'price': 'Obligatorio cuando venta_directa es true.'})

        return attrs

    def create(self, validated_data):
        if validated_data.get('fractionsTotal') is not None and validated_data.get('fractionsLeft') is None:
            validated_data['fractionsLeft'] = validated_data['fractionsTotal']
        validated_data['status'] = 'approved' if validated_data.get('venta_directa') else 'pending'
        return super().create(validated_data)

class ArtworkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artwork
        fields = [
            'title', 'description', 'price', 'fractionFrom', 'fractionsTotal',
            'image', 'gallery', 'tags'
        ]
        extra_kwargs = {
            'fractionFrom': {'required': False, 'allow_null': True},
            'fractionsTotal': {'required': False, 'allow_null': True},
        }
        partial = True

# Order Serializers
class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['artwork', 'fractions', 'paymentMethod']

class OrderSerializer(serializers.ModelSerializer):
    buyerId = serializers.CharField(source='buyer.id', read_only=True)
    artworkId = serializers.CharField(source='artwork.id', read_only=True)
    unitPrice = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    checkoutUrl = serializers.URLField(allow_null=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyerId', 'artworkId', 'fractions', 'unitPrice', 'amount',
            'status', 'checkoutUrl', 'createdAt'
        ]

# Favorite Serializers
class FavoriteResponseSerializer(serializers.Serializer):
    favorited = serializers.BooleanField()

# Artwork Stats Serializer
class ArtworkStatsSerializer(serializers.Serializer):
    artworkId = serializers.CharField()
    soldFractions = serializers.IntegerField()
    fractionsTotal = serializers.IntegerField()
    soldPct = serializers.FloatField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    timeline = serializers.ListField(child=serializers.DictField())
    buyersTop = serializers.ListField(child=serializers.DictField())

# Error Serializer
class ErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)

# Wallet Serializers
class WalletAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['address']

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'

# Bank Account Serializers
class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'
        read_only_fields = ['user']

# Auction Serializers
class AuctionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = ['start_price', 'start_date', 'end_date']

class AuctionSerializer(serializers.ModelSerializer):
    artwork_title = serializers.CharField(source='artwork.title', read_only=True)
    artwork_image = serializers.URLField(source='artwork.image.url', read_only=True)
    artist_name = serializers.CharField(source='artwork.artist.name', read_only=True)

    class Meta:
        model = Auction
        fields = '__all__'