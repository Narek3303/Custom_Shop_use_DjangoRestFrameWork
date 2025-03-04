from django.urls import path
from . import views


urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/category/<slug:category_slug>/', views.ProductListView.as_view(), name='product-list-by-category'),
    path('products/category/<slug:category_slug>/subcategory/<slug:subcategory_slug>/', views.ProductListView.as_view(), name='product-list-by-subcategory'),
    path('product-detail/<slug:slug>/<int:product_id>/', views.ProductDetailView.as_view(), name='product_detail'),
]