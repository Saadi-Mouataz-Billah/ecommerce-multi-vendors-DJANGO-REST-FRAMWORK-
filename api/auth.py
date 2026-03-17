from django.contrib.auth.backends import ModelBackend
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import User, Admin

# Auth user (because it's a specific model)
class UserAuth(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print("🚀 EmailBackend called!")
        print("username:", username, "password:", password)
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            print("❌ user not found")
            return None
        if user.check_password(password):
            print("✅ password ok for", user.email)
            return user
        else:
            print("❌ password incorrect")
        return None

# Auth admin (because it's a specific model)
class AdminAuth(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print("🚀 EmailBackend called!")
        print("username:", username, "password:", password)
        try:
            admin = Admin.objects.get(email=username)
        except Admin.DoesNotExist:
            print("❌ user not found")
            return None
        if admin.check_password(password):
            print("✅ password ok for", admin.email)
            return admin
        else:
            print("❌ password incorrect")
        return None

# Get the User from the token (important for multi-user types & models)
class MultiModelJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        print("🚀 MultiModelJWTAuthentication called!")
        print("user_id:", user_id)
        if not user_id:
            raise InvalidToken("Token contained no recognizable user identification")
        try:
            admin = Admin.objects.get(id=user_id)
            print("✅ Found admin:", admin.email)
            return admin
        except Admin.DoesNotExist:
            print("❌ Admin not found")
        try:
            user = User.objects.get(id=user_id)
            print("✅ Found user:", user.email)
            return user
        except User.DoesNotExist:
            raise InvalidToken("User not found")
        return None