from django.urls import path
from . import views
from .views import ProductListView, ProductFilterListView, ToggleWishlistView, WishlistProductsView, \
                    ReviewView, AdminReviewModeration, ProductPriceView, convert_price, \
                    SetCurrencyAPIView, GetAvailableCurrenciesAPIView, ProductHybridRecommendationView, ProductLikedView
from django.http import JsonResponse
from .models import SizePrice, Size


def get_product_sizes(request, product_id):
    sizes = Size.objects.filter(
        id__in=SizePrice.objects.filter(product_id=product_id).values_list('size_id', flat=True)
    ).values('id', 'name')

    return JsonResponse({
        'sizes': list(sizes)
    })


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
    path('wishlist/toggle/', ToggleWishlistView.as_view(), name='toggle-wishlist'),
    path('wishlist_all/', WishlistProductsView.as_view(), name='wishlist'),
    path('admin/reviews/<int:review_id>/', AdminReviewModeration.as_view(), name='review-moderation'),
    path('api/product/<int:product_id>/price/<str:currency_code>/', ProductPriceView.as_view(), name='product-price'),
    path('product/<int:product_id>/recommendations/<int:user_id>/', ProductHybridRecommendationView.as_view(), name='product_hybrid_recommendations'),


    path('product-detail/<slug:slug>/<int:product_id>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('api/accounts/user_token_check/', views.UserTokenCheckView.as_view()),
    path('convert_price/<int:product_id>/<str:currency_code>/', convert_price, name='convert_price'),
    path('api/set-currency/', SetCurrencyAPIView.as_view(), name='set_currency'),
    path('api/available-currencies/', GetAvailableCurrenciesAPIView.as_view(), name='available_currencies'),
    path("reviews/<int:product_id>/<int:review_id>/", ReviewView.as_view(), name="review-detail"),
    path("reviews/<int:product_id>/", ReviewView.as_view(), name="review-detail"),
    path("liked_products/", ProductLikedView.as_view(), name="liked_products"),
    path('admin/api/product/<int:product_id>/sizes/', get_product_sizes),


]



