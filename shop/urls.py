from django.urls import path
from . import views
from .views import ProductListView, ProductFilterListView


urlpatterns = [
    path('create-products/', views.create_products, name='create-products'),
    path('category/', views.CategoryView.as_view()),
    path('sliders/', views.SliderListAPIView.as_view()),
    path('product_filter/', views.ProductFilterView.as_view()),
    path('products/', ProductFilterListView.as_view(), name='product_list'),
    path('products_all/', views.ProductListView.as_view()),
    path('products/<slug:category_slug>/', ProductListView.as_view(), name='product_list_by_category'),
    path('products/<slug:category_slug>/<slug:subcategory_slug>/', ProductListView.as_view(),
         name='product_list_by_subcategory'),
    path('discounted_products/', views.ProductFilterDiscountedListView.as_view()),

    path('product-detail/<slug:slug>/<int:product_id>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('api/accounts/user_token_check/', views.UserTokenCheckView.as_view()),

]