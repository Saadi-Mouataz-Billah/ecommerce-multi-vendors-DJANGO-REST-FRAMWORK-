from . import views
from django.urls import path

urlpatterns = [
    # user
    path('register/', views.UserRegister.as_view(), name='register-user'),
    path('login/', views.UserLogin.as_view(), name='login-user'),
    path('activate-user/<uuid:pk>', views.ActivateUser.as_view(), name='activate-user'),
    path('deactivate-user/<uuid:pk>', views.DeactivateUser.as_view(), name='deactivate-user'),
    path('user/', views.UserList.as_view(), name='user-list'), # users list
    path('user/<uuid:pk>', views.UserDetail.as_view(), name='user-detail'), # update, delete, get by id

    # admin
    path('admin-register/', views.AdminRegister.as_view(), name='register'),
    path('admin-login/', views.AdminLogin.as_view(), name='admin-login'),
    path('activate-admin/<uuid:pk>', views.ActivateAdmin.as_view(), name='activate-admin'),
    path('deactivate-admin/<uuid:pk>', views.DeactivateAdmin.as_view(), name='deactivate-admin'),
    path('admin-list/', views.AdminList.as_view(), name='admin-list'),
    path('admin-details/<uuid:pk>', views.AdminDetail.as_view(), name='admin-details'),

    # store
    path('stores/', views.StoreList.as_view(), name='stores-list'),
    path('user-stores/', views.UserStoreList.as_view(), name='user-store-list'),
    path('store/<uuid:pk>', views.StoreDetail.as_view(), name='store-detail'),
    path('activate-store/<uuid:pk>', views.ActivateStore.as_view(), name='activate-store'),
    path('deactivate-store/<uuid:pk>', views.DeactivateStore.as_view(), name='deactivate-store'),

    # category
    path('category/', views.CategoryList.as_view(), name='category-list'),
    path('category/<uuid:pk>', views.CategoryDetail.as_view(), name='category-detail'),

    # brand
    path('brand/', views.BrandList.as_view(), name='brand-list'),
    path('brand/<uuid:pk>', views.BrandDetail.as_view(), name='brand-detail'),

    # all products
    path('product/', views.ProductList.as_view(), name='product-list'),
    path('store-product/<uuid:pk>', views.StoreProductList.as_view(), name='store-product-list'),

    # products
    path('simple-products/', views.SimpleProductList.as_view(), name='simple-product-list'),
    path('simple-products/<uuid:pk>', views.SimpleProductDetail.as_view(), name='simple-product-detail'),
    path('configurable-products/', views.ConfigurableProductList.as_view(), name='config-product-list'),
    path('configurable-products/<uuid:pk>', views.ConfigurableProductDetail.as_view(), name='config-product-detail'),
    path('customisable-products/', views.CustomisableProductList.as_view(), name='custom-product-list'),
    path('customisable-products/<uuid:pk>', views.CustomisableProductDetail.as_view(), name='custom-product-detail'),
]
