from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bulk-update/', views.bulk_update, name='bulk_update'),
    path('product/new/', views.product_create, name='product_create'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('product/<int:pk>/archive/', views.product_archive, name='product_archive'),
    path('product/<int:pk>/unarchive/', views.product_unarchive, name='product_unarchive'),
    path('product/<int:pk>/variant/add/', views.variant_create, name='variant_create'),
    path('variant/<int:pk>/edit/', views.variant_edit, name='variant_edit'),
    path('variant/<int:pk>/delete/', views.variant_delete, name='variant_delete'),
    # Import disabled per request
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/xlsx/', views.export_xlsx, name='export_xlsx'),
]
