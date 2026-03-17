from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from phonenumber_field.modelfields import PhoneNumberField

# User and Admin
class BaseUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    email = models.EmailField(unique=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="%(class)s_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="%(class)s_permissions",
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    class Meta:
        abstract = True

# USER
class User(BaseUser):
    picture = models.ImageField(upload_to='images/user_pfp', null=False, blank=False)
    phone = PhoneNumberField(region="DZ", null=False, blank=False)
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return self.email

# ADMIN
class Admin(BaseUser):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        SUPERADMIN = 'superadmin'
    username = models.CharField(null=False, blank=False, unique=False, max_length=150)
    role = models.CharField(choices=Role.choices, max_length=20, null=False, blank=False)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.email

# STORE
class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User, on_delete= models.CASCADE, null= False, blank=False, related_name='stores')
    name = models.CharField(max_length=200, null=False, blank=False)
    logo = models.ImageField(upload_to='images/store-logo', null=False, blank=False)
    is_active = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

# CATEGORY
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200, unique=True, null=False, blank=False)
    logo = models.ImageField(upload_to='images/category-logo', null=False, blank=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

# BRAND
class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200, null=False, blank=False)
    category = models.ForeignKey(Category, on_delete= models.CASCADE, null=False, blank=False, related_name='brands')
    logo = models.ImageField(upload_to='images/brand-logo', null=False, blank=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

# PRODUCTS
class Product(models.Model):
    class Type(models.TextChoices):
        SIMPLE = 'simple'
        CONFIGURABLE = 'configurable'
        CUSTOMISABLE = 'customisable'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    type = models.CharField(choices=Type.choices, max_length=20, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete= models.CASCADE, null= False, blank=False)
    store = models.ForeignKey(Store, on_delete= models.CASCADE, null=False, blank=False)
    brand = models.ForeignKey(Brand, on_delete= models.CASCADE, null=True, blank=True)
    sold = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class SimpleProduct(Product):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='simple_products')
    price = models.PositiveIntegerField(null=False, blank=False)
    stock = models.PositiveIntegerField(null=False, blank=False)
    def __str__(self):
        return self.name
    def in_stock(self):
        return self.stock > 0

class ConfigurableProduct(Product):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='configurable_products')
    price = models.PositiveIntegerField(null=False, blank=False)
    def __str__(self):
        return self.name

class Option(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    configurableProduct = models.ForeignKey(ConfigurableProduct, on_delete= models.CASCADE, null=False, blank=False, related_name='options')
    data = models.JSONField()
    stock = models.PositiveIntegerField(null=False, blank=False)
    def __str__(self):
        return f"Option ({self.id}) for configurable product ({self.configurableProduct.id})"
    def in_stock(self):
        return self.stock > 0

class CustomisableProduct(Product):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='customisable_products')
    def __str__(self):
        return self.name

class Variant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    customisableProduct = models.ForeignKey(CustomisableProduct, on_delete= models.CASCADE, null=False, blank=False, related_name='variants')
    price = models.PositiveIntegerField(null=False, blank=False)
    stock = models.PositiveIntegerField(null=False, blank=False)
    data = models.JSONField(default=dict)
    def __str__(self):
        return f"Variant ({self.id}) for customisable product ({self.customisableProduct.id})"

# CART
class CartItems(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    product_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=False, blank=False)
    prod_id = models.UUIDField(null=False, blank=False)
    product = GenericForeignKey('product_type', 'prod_id')
    order = models.ForeignKey(Order, on_delete= models.CASCADE, null=False, blank=False, related_name='cart_items')
    quantity= models.PositiveIntegerField(null= False, blank=False, default= 1)
    def item_subtotal(self):
        if self.product is None:
            return 0
        prod_type = getattr(self.product, 'type', None)
        price = getattr(self.product, 'price', 0)
        if prod_type in ['simple', 'configurable']:
            return self.quantity * price
        elif prod_type == 'customisable':
            variants = getattr(self.product, 'variants', None)
            if variants and getattr(variants, 'price', 0):
                return self.quantity * variants.price
        return 0
    def __str__(self):
        return f"{self.quantity} X {self.product.name} in order: {self.order.id}"

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_cart')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Cart {self.id} by {self.user.username}"
# ORDER
class OrderItems(models.Model):
    pass

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        CONFIRMED = 'confirmed'
        CANCELLED = 'cancelled'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Order {self.id} by {self.user.username}"