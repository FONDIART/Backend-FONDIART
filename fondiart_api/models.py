from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone

# Custom User Model (extending AbstractUser for flexibility)
class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('artist', 'Artist'),
        ('admin', 'Admin'),
    )
    name = models.CharField(max_length=255, blank=True) # Add name field
    dni = models.CharField(max_length=20, blank=True, null=True) # Add dni field
    email = models.EmailField(unique=True) # Ensure email is unique
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    avatarUrl = models.URLField(max_length=200, blank=True, null=True)
    # Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(Group, related_name='fondiart_users', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='fondiart_users_permissions', blank=True)
    phone = models.CharField(max_length=255, blank=True) # Add name field
    bio = models.TextField(blank=True, null=True) # Add bio field
    cbu = models.CharField(max_length=22, blank=True, null=True) # Add cbu field
    
    


    def __str__(self):
        return self.email

    # Override create_user to handle 'name'
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self._create_user(username, email, password, **extra_fields)
        if 'name' in extra_fields:
            user.name = extra_fields['name']
            user.save(update_fields=['name'])
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin') # Set admin role for superuser
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, email, password, **extra_fields)

# Artwork Model
class Artwork(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artworks')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    fractionFrom = models.DecimalField(max_digits=10, decimal_places=2) # Assuming this is a decimal for fractional ownership
    fractionsTotal = models.IntegerField()
    fractionsLeft = models.IntegerField()
    tags = models.JSONField(default=list) # Storing tags as a JSON list
    image = models.URLField(max_length=200)
    gallery = models.JSONField(default=list) # Storing gallery images as a JSON list of URLs
    createdAt = models.DateTimeField(auto_now_add=True)
    approvedAt = models.DateTimeField(blank=True, null=True)

    # Rating fields
    rating_avg = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title

# Order Model
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    )
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='orders')
    fractions = models.IntegerField()
    unitPrice = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    paymentMethod = models.CharField(max_length=10) # card, pix, bank, test
    checkoutUrl = models.URLField(max_length=200, blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.email} for {self.artwork.title}"

# Favorite Model
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='favorites')
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artwork') # A user can favorite an artwork only once

    def __str__(self):
        return f"{self.user.email} favorited {self.artwork.title}"

# Wallet Model
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    address = models.CharField(max_length=42, unique=True)
    private_key = models.CharField(max_length=64)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Wallet for {self.user.email}"

# Bank Account Model
class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    owner_name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"Bank Account for {self.user.email}"
