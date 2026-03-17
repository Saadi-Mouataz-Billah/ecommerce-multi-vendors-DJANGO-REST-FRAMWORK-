from rest_framework_simplejwt.tokens import RefreshToken

def get_user_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh['type'] = 'user'
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_admin_tokens(admin):
    refresh = RefreshToken.for_user(admin)
    refresh['type'] = 'admin'
    refresh['role'] = admin.role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }




# IF WE HAVE ONLY 1 CLASS USER WITH DIFFERENT ROLES (USER, ADMIN, SUPERADMIN) WE USE TOKEN LIKE THIS:
#from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

#class CustomUserToken(TokenObtainPairSerializer):
##    @class-method
# def get_token(cls, user):
#       token = super().get_token(user)
        # Add custom claims
#        token['role'] = user.role
#        token['email'] = user.email
#        return token
#    def validate(self, attrs):
#        data = super().validate(attrs)
#        data['role'] = self.user.role
#        data['email'] = self.user.email
#        return data