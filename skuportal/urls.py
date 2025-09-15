from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from inventory import views as inv_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('store/', inv_views.store_index, name='store_index'),
    path('store/cart/', inv_views.store_cart, name='store_cart'),
    path('store/checkout/', inv_views.store_checkout, name='store_checkout'),
    path('store/<int:vid>/', inv_views.store_product, name='store_product'),
    path('signup/', inv_views.signup, name='signup'),
    path('', include('inventory.urls', namespace='inventory')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
