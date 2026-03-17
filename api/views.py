from itertools import chain
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import *
from rest_framework.views import APIView
from .permissions import *
from .serializers import *
from .models import *
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from .tokens import *

# USER VIEWS
class UserRegister(generics.CreateAPIView): # ✅ Work
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserLogin(APIView): # ✅ Work
    permission_classes = [AllowAny]
    def post(self, request): # noqa
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user and isinstance(user, User):
            if not user.is_active:
                return Response({'message': 'User not activated. Please wait until activation'},
                                status=status.HTTP_400_BAD_REQUEST)
            tokens = get_user_tokens(user)
            return Response({'tokens': tokens, 'user': user.email})
        return Response({'detail': 'Invalid Email or Password.'}, status=status.HTTP_401_UNAUTHORIZED)

class UserList(generics.ListAPIView): # ✅ Work
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin | IsAdmin]


class UserDetail(generics.RetrieveUpdateDestroyAPIView): # ✅ Work
    queryset = User.objects.all()
    serializer_class = UserSerializer
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'PATCH']:
            permission_classes = [IsUser]
        elif self.request.method == 'DELETE':
            permission_classes = [IsSuperAdmin | IsAdmin]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not user.is_active:
            raise PermissionDenied(f"User {user.username} is not active")
        if self.request.method == 'DELETE':
            return qs.exclude(id=user.id)
        return qs.filter(id=user.id)
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        username = instance.username
        self.perform_destroy(instance)
        return Response(
            {'message': f"User '{username}' deleted successfully."},
            status=status.HTTP_200_OK
        )

class ActivateUser(generics.UpdateAPIView): # ✅ Work
    queryset = User.objects.all()
    serializer_class = UserStatusSerializer
    permission_classes = [IsSuperAdmin | IsAdmin]
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_active:
            return Response({'message': 'User is already activated'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save()
        return Response({'detail': f'User {user.email} has been activated'})

class DeactivateUser(generics.UpdateAPIView): # ✅ Work
    queryset = User.objects.all()
    serializer_class = UserStatusSerializer
    permission_classes = [IsSuperAdmin | IsAdmin]
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if not user.is_active:
            return Response({'message': 'User is already deactivated'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = False
        user.save()
        return Response({'detail': f'User {user.email} has been deactivated'})

# ADMIN VIEWS
class AdminRegister(generics.CreateAPIView): # ✅ Work
    serializer_class = AdminSerializer
    permission_classes = [IsSuperAdmin]

class AdminLogin(APIView): # ✅ Work
    permission_classes = [AllowAny]
    def post(self, request): # noqa
        email = request.data.get('email')
        password = request.data.get('password')
        admin = authenticate(request, username=email, password=password)
        if admin and isinstance(admin, Admin):
            if not admin.is_active:
                return Response({'message': 'Admin not activated. Please wait until activation'},
                                status=status.HTTP_400_BAD_REQUEST)
            tokens = get_admin_tokens(admin)
            return Response({'tokens': tokens, 'admin': admin.email, 'role': admin.role})
        return Response({'detail': 'Invalid Email or Password.'}, status=status.HTTP_401_UNAUTHORIZED)

class ActivateAdmin(generics.UpdateAPIView): # ✅ Work
    queryset = Admin.objects.all()
    serializer_class = AdminStatusSerializer
    permission_classes = [IsSuperAdmin]
    def update(self, request, *args, **kwargs):
        admin = self.get_object()
        if admin.is_active:
            return Response({'message': 'Admin is already activated'}, status=status.HTTP_400_BAD_REQUEST)
        admin.is_active = True
        admin.save()
        return Response({'detail': f'Admin {admin.email} has been activated'})

class DeactivateAdmin(generics.UpdateAPIView): # ✅ Work
    queryset = Admin.objects.all()
    serializer_class = AdminStatusSerializer
    permission_classes = [IsSuperAdmin]
    def update(self, request, *args, **kwargs):
        admin = self.get_object()
        if not admin.is_active:
            return Response({'message': 'Admin is already deactivated'}, status=status.HTTP_400_BAD_REQUEST)
        admin.is_active = False
        admin.save()
        return Response({'detail': f'Admin {admin.email} has been deactivated'})

class AdminList(generics.ListAPIView): # ✅ Work
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsSuperAdmin]
    def get_queryset(self):
        return Admin.objects.filter(role__in=[Admin.Role.ADMIN])

class AdminDetail(generics.RetrieveUpdateDestroyAPIView): # # ✅ Work
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'PATCH']:
            permission_classes = [IsSuperAdmin | IsAdmin]
        elif self.request.method == 'DELETE':
            permission_classes = [IsSuperAdmin]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        admin = self.request.user
        qs = super().get_queryset()
        if not admin.is_active:
            raise PermissionDenied(f"User {admin.email} is not active")
        if admin.role == Admin.Role.ADMIN:
            return qs.filter(id=admin.id)
        if admin.role == Admin.Role.SUPERADMIN:
            return qs.filter(role__in=[Admin.Role.ADMIN, Admin.Role.SUPERADMIN])
        return qs.none()
    def perform_update(self, serializer):
        admin = self.request.user
        instance = self.get_object()
        if admin.role == Admin.Role.SUPERADMIN and instance.id != admin.id:
            raise PermissionDenied("SuperAdmin can only update his own account.")
        if admin.role == Admin.Role.ADMIN and instance.id != admin.id:
            raise PermissionDenied("Admin can only update his own account.")
        serializer.save()
    def perform_destroy(self, instance):
        admin = self.request.user
        if admin.role == Admin.Role.ADMIN:
            raise PermissionDenied("Admin cannot delete accounts.")
        if admin.role == Admin.Role.SUPERADMIN and instance.id == admin.id:
            raise PermissionDenied("SuperAdmin cannot delete his own account.")
        if admin.role == Admin.Role.SUPERADMIN and instance.role == Admin.Role.ADMIN:
            instance.delete()
            return
        raise PermissionDenied("SuperAdmin can only delete Admin accounts.")
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        email = instance.email
        self.perform_destroy(instance)
        return Response(
            {'message': f"Admin '{email}' deleted successfully."},
            status=status.HTTP_200_OK
        )

# STORE VIEWS
class StoreList(generics.ListAPIView): # ✅ Work
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [AllowAny]

class UserStoreList(generics.ListCreateAPIView): # ✅ Work
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsUser | IsSuperAdmin | IsAdmin]
        elif self.request.method == 'POST':
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'role', None) in [Admin.Role.SUPERADMIN, Admin.Role.ADMIN]: # SuperAdmin, Admin can see all users stores
            return qs
        return qs.filter(user=user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        if Store.objects.filter(name=name).exists():
            return Response({'message': f'Store ({name}) already exists'},
                                              status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

class StoreDetail(generics.RetrieveUpdateDestroyAPIView): # ✅ Work
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsUser]
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsUser | IsSuperAdmin | IsAdmin]
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if isinstance(user, User):
            return qs.filter(user=user)
        if getattr(user, 'role', None) in [Admin.Role.SUPERADMIN, Admin.Role.ADMIN]:
            return qs
        return qs.none()
    def get_object(self):
        store = super().get_object()
        if not store.is_active:
            raise PermissionDenied(f"Store ({store.name}) isn't active yet. Please wait until activation.")
        return store
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response(
            {'message': f"Store '{name}' deleted successfully."},
            status=status.HTTP_200_OK
        )

class ActivateStore(generics.UpdateAPIView): # ✅ Work
    queryset = Store.objects.all()
    serializer_class = StoreStatusSerializer
    permission_classes = [IsSuperAdmin | IsAdmin]
    def update(self, request, *args, **kwargs):
        store = self.get_object()
        if store.is_active:
            return Response({'message': 'Store is already activated'},
                            status=status.HTTP_400_BAD_REQUEST)
        store.is_active = True
        store.save()
        return Response({'detail': f'Store {store.name} has been activated'})

class DeactivateStore(generics.UpdateAPIView): # ✅ Work
    queryset = Store.objects.all()
    serializer_class = StoreStatusSerializer
    permission_classes = [IsSuperAdmin | IsAdmin]
    def update(self, request, *args, **kwargs):
        store = self.get_object()
        if not store.is_active:
            return Response({'message': 'Store is already deactivated'}, status=status.HTTP_400_BAD_REQUEST)
        store.is_active = False
        store.save()
        return Response({'detail': f'Store ({store.name}) has been deactivated'})

# CATEGORY VIEWS
class CategoryList(generics.ListCreateAPIView): # ✅ Work
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        elif self.request.method == 'POST':
            permission_classes = [IsSuperAdmin | IsAdmin]
        return [permission() for permission in permission_classes]
    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        if Category.objects.filter(name=name).exists():
            return Response({'detail': f'Category already exists!'},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

class CategoryDetail(generics.RetrieveUpdateDestroyAPIView): # ✅ Work
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsSuperAdmin | IsAdmin]
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response(
            {'message': f"Category '{name}' deleted successfully."},
            status=status.HTTP_200_OK
        )

# BRAND VIEWS
class BrandList(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        elif self.request.method == 'POST':
            permission_classes = [IsSuperAdmin | IsAdmin]
        return [permission() for permission in permission_classes]
    def create(self, request, *args, **kwargs):
        category_id = request.data.get('category')
        if not category_id:
            return Response({'detail': 'Category field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not Category.objects.filter(id=category_id).exists():
            return Response({'detail': f'Selected category not found!'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

class BrandDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsSuperAdmin | IsAdmin]
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response(
            {'message': f"Brand '{name}' deleted successfully."},
            status=status.HTTP_200_OK
        )

# ALL PRODUCTS VIEWS
class ProductList(generics.ListAPIView):
    serializer_class = AllProductsTypeSerializer
    def get_queryset(self):
        simple = SimpleProduct.objects.all()
        configurable = ConfigurableProduct.objects.all()
        customisable = CustomisableProduct.objects.all()
        return list(chain(simple, configurable, customisable)) # type: ignore
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class StoreProductList(generics.ListAPIView):
    serializer_class = AllProductsTypeSerializer
    def get_queryset(self):
        store = getattr(self.request.user, 'store', None) # if user does not have any store return empty list
        if not store:
            return Response('User does not have store', status=status.HTTP_403_FORBIDDEN)
        simple = SimpleProduct.objects.filter(store=store)
        configurable = ConfigurableProduct.objects.filter(store=store)
        customisable = CustomisableProduct.objects.filter(store=store)
        return list(chain(simple, configurable, customisable)) # type: ignore
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# PRODUCTS VIEWS
class SimpleProductList(generics.ListCreateAPIView): # test
    queryset = SimpleProduct.objects.all()
    serializer_class = SimpleProductSerializer
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) in [Admin.Role.SUPERADMIN, Admin.Role.ADMIN]:
            return SimpleProduct.objects.all()
        elif isinstance(user, User):
            stores = getattr(user, 'store', None)
            if stores and stores.exists(): return SimpleProduct.objects.filter(store=user.store)
            return SimpleProduct.objects.none()
        return SimpleProduct.objects.none()
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsUser | IsSuperAdmin | IsAdmin]
        elif self.request.method == 'POST':
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def perform_create(self, serializer):
        user = self.request.user
        store_id = self.request.data.get("store")
        if not store_id:
            raise PermissionDenied("Please select a store before adding a product.")
        store = user.stores.filter(id=store_id).first()
        if not store:
            raise PermissionDenied("You can only add products to your own stores.")
        serializer.save(store=store)
    def create(self, request, *args, **kwargs):
        user = request.user
        store_id = self.request.data.get("store")
        if not store_id:
            raise PermissionDenied("Please select a store before adding a product.")
        store = user.stores.filter(id=store_id).first()
        name = request.data.get('name')
        if SimpleProduct.objects.filter(name=name, store= store).exists():
            return Response({'detail': f"Simple products '{name}' already exists in this store!"},
                            status=status.HTTP_400_BAD_REQUEST)
        response = super().create(request, *args, **kwargs)
        return Response({"message": "Simple Product created successfully.", "data": response.data},
            status=status.HTTP_201_CREATED
        )

class SimpleProductDetail(generics.RetrieveUpdateDestroyAPIView): # test
    queryset = SimpleProduct.objects.all()
    serializer_class = SimpleProductSerializer
    def get_permissions(self):
        if self.request.method in ['GET', 'DELETE']:
            permission_classes = [IsSuperAdmin | IsAdmin | IsUser]
        if self.request.method in ['PUT', 'PATCH']:
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({'message': f"Simple product '{name}' deleted successfully."},
                               status=status.HTTP_200_OK)

class ConfigurableProductList(generics.ListCreateAPIView):  # test
    queryset = ConfigurableProduct.objects.prefetch_related('options')
    serializer_class = ConfigurableProductSerializer
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) in [Admin.Role.SUPERADMIN, Admin.Role.ADMIN]:
            return ConfigurableProduct.objects.prefetch_related('options')
        elif isinstance(user, User):
            stores = getattr(user, 'stores', None)
            if stores and stores.exists():
                return ConfigurableProduct.objects.filter(store__in=user.stores.all()).prefetch_related('options')
            return ConfigurableProduct.objects.none()
        return ConfigurableProduct.objects.none()
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsUser | IsSuperAdmin | IsAdmin]
        elif self.request.method == 'POST':
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def perform_create(self, serializer):
        user = self.request.user
        store_id = self.request.data.get("store")
        if not store_id:
            raise PermissionDenied("Please select a store before adding a product.")
        store = user.stores.filter(id=store_id).first()
        if not store:
            raise PermissionDenied("You can only add products to your own stores.")
        serializer.save(store=store)
    def create(self, request, *args, **kwargs):
        user = request.user
        store_id = request.data.get("store")
        # 🧩 Vérification du store
        if not store_id:
            raise PermissionDenied("Please select a store before adding a product.")
        store = user.stores.filter(id=store_id).first()
        if not store:
            raise PermissionDenied("You can only add products to your own stores.")
        # 🧩 Vérification de nom unique
        name = request.data.get('name')
        if ConfigurableProduct.objects.filter(name=name, store=store).exists():
            return Response(
                {'detail': f"Configurable product '{name}' already exists in this store!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # 🧩 Préparation des données
        options_raw = request.data.get('options')
        data = dict(request.data)# ⚠️ نعمل dict عادي بدل QueryDict
        for key, val in data.items():
            if isinstance(val, list) and len(val) == 1:
                data[key] = val[0]
        if options_raw: # ✅ نفكّ JSON تاع options
            try:
                data['options'] = json.loads(options_raw)
            except json.JSONDecodeError:
                return Response({'options': ['Invalid JSON format.']}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'options': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        # 🧩 Validation et création
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Configurable Product created successfully.","data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

class ConfigurableProductDetail(generics.RetrieveUpdateDestroyAPIView):  # test
    queryset = ConfigurableProduct.objects.prefetch_related('options')
    serializer_class = ConfigurableProductSerializer
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) in [Admin.Role.SUPERADMIN, Admin.Role.ADMIN]:
            return ConfigurableProduct.objects.prefetch_related('options')
        if isinstance(user, User):
            stores = getattr(user, 'stores', None)
            if stores and stores.exists():
                return ConfigurableProduct.objects.filter(store__in=stores.all()).prefetch_related('options')
        return ConfigurableProduct.objects.none()
    def get_permissions(self):
        if self.request.method in ['GET', 'DELETE']:
            permission_classes = [IsSuperAdmin | IsAdmin | IsUser]
        if self.request.method in ['PUT', 'PATCH']:
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def update(self, request, *args, **kwargs):
        data = dict(request.data)
        for key, val in data.items():
            if isinstance(val, list) and len(val) == 1:
                data[key] = val[0]
        options_raw = data.get('options')
        if options_raw:
            try:
                data['options'] = json.loads(options_raw)
            except json.JSONDecodeError:
                return Response({'options': ['Invalid JSON format.']}, status=status.HTTP_400_BAD_REQUEST)
        partial = kwargs.pop('partial', True)
        serializer = self.get_serializer(self.get_object(), data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": "Configurable Product updated successfully.", "data": serializer.data})
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({'message': f"Configurable product '{name}' deleted successfully."},
                               status=status.HTTP_200_OK)

class CustomisableProductList(generics.ListCreateAPIView):  # test
    queryset = CustomisableProduct.objects.prefetch_related('variants')
    serializer_class = CustomisableProductSerializer
    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) in [Admin.Role.SUPERADMIN, Admin.Role.ADMIN]:
            return CustomisableProduct.objects.prefetch_related('variants')
        elif isinstance(user, User):
            stores = getattr(user, 'stores', None)
            if stores and stores.exists(): return CustomisableProduct.objects.filter(store__in=user.stores.all()).prefetch_related('variants')
            return CustomisableProduct.objects.none()
        return CustomisableProduct.objects.none()
    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsUser | IsSuperAdmin | IsAdmin]
        elif self.request.method == 'POST':
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def perform_create(self, serializer):
        user = self.request.user
        store_id = self.request.data.get("store")
        if not store_id:
            raise PermissionDenied("Please select a store before adding a product.")
        store = user.stores.filter(id=store_id).first()
        if not store:
            raise PermissionDenied("You can only add products to your own stores.")
        serializer.save(store=store)
    def create(self, request, *args, **kwargs):
        user = request.user
        store_id = request.data.get("store")
        # 🧩 Vérification du store
        if not store_id:
            raise PermissionDenied("Please select a store before adding a product.")
        store = user.stores.filter(id=store_id).first()
        if not store:
            raise PermissionDenied("You can only add products to your own stores.")
        # 🧩 Vérification de nom unique
        name = request.data.get('name')
        if CustomisableProduct.objects.filter(name=name, store=store).exists():
            return Response(
                {'detail': f"Customisable product '{name}' already exists in this store!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # 🧩 Préparation des données
        variants_raw = request.data.get('variants')
        data = dict(request.data)  # ⚠️ نعمل dict عادي بدل QueryDict
        for key, val in data.items():
            if isinstance(val, list) and len(val) == 1:
                data[key] = val[0]
        if variants_raw:  # ✅ نفكّ JSON تاع variants
            try:
                data['variants'] = json.loads(variants_raw)
            except json.JSONDecodeError:
                return Response({'variants': ['Invalid JSON format.']}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'variants': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        # 🧩 Validation et création
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Customisable Product created successfully.", "data": serializer.data},
                        status=status.HTTP_201_CREATED,
                        )

class CustomisableProductDetail(generics.RetrieveUpdateDestroyAPIView):  # test
    queryset = CustomisableProduct.objects.all()
    serializer_class = CustomisableProductSerializer
    def get_permissions(self):
        if self.request.method in ['GET', 'DELETE']:
            permission_classes = [IsSuperAdmin | IsAdmin | IsUser]
        if self.request.method in ['PUT', 'PATCH']:
            permission_classes = [IsUser]
        return [permission() for permission in permission_classes]
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({'message': f"Customisable product '{name}' deleted successfully."},
                               status=status.HTTP_200_OK)
    def update(self, request, *args, **kwargs):
        data = dict(request.data)
        for key, val in data.items():
            if isinstance(val, list) and len(val) == 1:
                data[key] = val[0]
        variants_raw = data.get('variants')
        if variants_raw:
            try:
                data['variants'] = json.loads(variants_raw)
            except json.JSONDecodeError:
                return Response({'variants': ['Invalid JSON format.']}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(self.get_object(), data=data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": "Customisable Product updated successfully.", "data": serializer.data})

    # test all products

# CART


# ORDER
