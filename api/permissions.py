from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import User

def get_role(user):
    return getattr(user, 'role', None)

class IsUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS: # 👁️ السماح بالقراءة للجميع (GET, HEAD, OPTIONS)
            return True
        if hasattr(obj, "user"): # إذا الموديل عنده user مباشرة (مثلاً Store)
            return obj.user == request.user
        if hasattr(obj, "store") and hasattr(obj.store, "user"): # إذا الموديل مرتبط بمتجر (مثلاً ConfigurableProduct)
            return obj.store.user == request.user
        return False # إذا لا يوجد ارتباط، نمنع التعديل
    def has_permission(self, request, view):
       if not request.user or not request.user.is_authenticated:
           return False
       return isinstance(request.user, User)

    #def has_object_permission(self, request, view, obj):
    #    if request.method in SAFE_METHODS: # Anyone can read
    #        return True
    #    return obj.user == request.user # Only store owner can update or delete only his own store

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        role = get_role(request.user)
        return role == 'admin'

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        role = get_role(request.user)
        return role == 'superadmin'

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        role = get_role(request.user)
        return role in ['admin', 'superadmin']
