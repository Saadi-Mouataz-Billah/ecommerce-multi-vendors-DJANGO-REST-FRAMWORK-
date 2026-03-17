from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import *
import json

# USER & ADMIN
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'picture', 'phone', 'is_staff', 'is_superuser', 'is_active', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt', 'is_staff', 'is_superuser']
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    def create(self, validated_data):
        user = self.Meta.model(**validated_data)
        user.set_password(validated_data['password'])
        user.is_staff = False
        user.is_superuser= False
        user.save()
        return user

class AdminSerializer(serializers.ModelSerializer):
    role = serializers.CharField(default= Admin.Role.ADMIN)
    class Meta:
        model = Admin
        fields = ['id', 'email', 'password' ,'role', 'is_staff', 'is_superuser', 'is_active', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt', 'is_staff', 'is_superuser']
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    def validate_email(self, value):
        if Admin.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    def create(self, validated_data):
        admin = self.Meta.model(**validated_data)
        admin.set_password(validated_data['password'])
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save()
        return admin

class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'is_active']
        read_only_fields = ['id']

class AdminStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['id', 'is_active']
        read_only_fields = ['id']

# STORE
class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt', 'is_active', 'user']

class StoreStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'is_active']
        read_only_fields = ['id']

# CATEGORY
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt']

# BRAND
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt']

# ALL PRODUCTS
class AllProductsTypeSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, SimpleProduct):
            return SimpleProductSerializer(instance).data
        elif isinstance(instance, ConfigurableProduct):
            return ConfigurableProductSerializer(instance).data
        elif isinstance(instance, CustomisableProduct):
            return CustomisableProductSerializer(instance).data
        return super().to_representation(instance)

# PRODUCTS
class SimpleProductSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=Product.Type.choices, default=Product.Type.SIMPLE)
    class Meta:
        model = SimpleProduct
        fields = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt']
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

# configurable Prod
class OptionSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        data = rep.pop('data', {})  # extract original data
        if isinstance(data, dict):
            rep.update(data)  # integrate it inside rep
        return rep
    def to_internal_value(self, data):
        dynamic_fields = {}
        stock = data.get("stock")
        for key, value in data.items():
            if key != "stock": dynamic_fields[key] = value
        return { "data": dynamic_fields, "stock": stock }
    class Meta:
        model = Option
        fields = '__all__'
        read_only_fields = ['id', 'configurableProduct']

class ConfigurableProductSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=Product.Type.choices, default=Product.Type.CONFIGURABLE)
    #options = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all(), write_only=True)
    options = OptionSerializer(many=True, write_only=True)
    #option_detail = OptionSerializer(source='options', read_only=True)
    class Meta:
        model = ConfigurableProduct
        fields = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt']
    def create(self, validated_data):
       option_data = validated_data.pop('options')
       configurable_product = ConfigurableProduct.objects.create(**validated_data)
       print("✅ VALIDATED OPTIONS:", option_data)
       for opt in option_data:
          Option.objects.create(configurableProduct=configurable_product, **opt)
       return configurable_product
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['options'] = OptionSerializer(instance.options.all(), many=True).data
        return rep
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

# customisable Prod
class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = '__all__'
        read_only_fields = ['id', 'customisableProduct']
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.data:
            rep.update(instance.data)
        rep.pop('data', None)
        return rep

    def to_internal_value(self, data):
        base_fields = {'price', 'stock'}
        dynamic_data = {k: v for k, v in data.items() if k not in base_fields}
        internal = super().to_internal_value({k: v for k, v in data.items() if k in base_fields})
        internal['data'] = dynamic_data
        return internal

class CustomisableProductSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=Product.Type.choices, default=Product.Type.CUSTOMISABLE)
    variants = VariantSerializer(many=True, write_only=True)
    #variant = serializers.PrimaryKeyRelatedField(queryset=Variant.objects.all(), write_only=True)
    #variant_detail = VariantSerializer(source='variant', read_only=True)
    class Meta:
        model = CustomisableProduct
        fields = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt']
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['variants'] = VariantSerializer(instance.variants.all(), many=True).data
        return rep
    def create(self, validated_data):
        variant_data = validated_data.pop('variants')
        customisable_product = CustomisableProduct.objects.create(**validated_data)
        print("✅ VALIDATED VARIANTS:", variant_data)
        for var in variant_data:
            Variant.objects.create(customisableProduct=customisable_product, **var)
        return customisable_product

# CART


# ORDER