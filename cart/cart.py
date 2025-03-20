# from decimal import Decimal
# from django.conf import settings
# from shop.models import Product
# from coupon.models import Coupon
# from .serializers import ProductSerializer
#
# class Cart:
#     def __init__(self, request):
#         self.session = request.session
#         self.cart = self.session.get(settings.CART_SESSION_ID, {})
#         self.request = request
#         self.coupon = None
#         self.discount = Decimal(0)
#         self._products_cache = None  # 🔥 Ապրանքների cache
#
#         # Վերականգնում ենք կուպոնը session-ից
#         coupon_code = self.session.get('coupon_code')
#         if coupon_code:
#             self._load_coupon(coupon_code)
#
#     def _load_coupon(self, code):
#         """Helper ֆունկցիա՝ կուպոնի վերականգնման համար"""
#         try:
#             self.coupon = Coupon.objects.get(code=code)
#             self.discount = self.get_total_price() * (self.coupon.discount / 100)
#         except Coupon.DoesNotExist:
#             self.coupon = None
#             self.discount = Decimal(0)
#
#     def _get_products(self):
#         """Cache-ավորում ենք ապրանքները"""
#         if self._products_cache is None:
#             product_ids = self.cart.keys()
#             self._products_cache = {str(p.id): p for p in Product.objects.filter(id__in=product_ids)}
#         return self._products_cache
#
#     def __iter__(self):
#         """
#         Iterate over the items in the cart and get the products
#         from the database.
#         """
#         cart = self.cart.copy()
#
#         # Վերցնում ենք միայն product_id-ները (թվային արժեքները)
#         product_ids = [key.split("_")[0] for key in cart.keys()]
#
#         # Get the actual products from the database
#         products = Product.objects.filter(id__in=product_ids)
#
#         # Create a product map for easier lookup
#         product_map = {str(product.id): product for product in products}
#
#         # Iterate over the cart items
#         for product_id, item in cart.items():
#             base_product_id = product_id.split("_")[0]  # Extract numeric part
#             product = product_map.get(base_product_id)
#             if product:
#                 item['product'] = product
#                 item['price'] = Decimal(item.get('price', 0))  # Safe get for price
#                 item['total_price'] = item['price'] * item['quantity']
#             else:
#                 # Handle missing product case
#                 item['product'] = None
#                 item['price'] = Decimal(0)
#                 item['total_price'] = Decimal(0)
#
#             yield item
#
#     def __len__(self):
#         """Վերադարձնում է զամբյուղի ընդհանուր ապրանքների քանակը"""
#         return sum(item['quantity'] for item in self.cart.values())
#
#     def add(self, product, colors, size, price, final_price, quantity=1, override=False):
#         """Ավելացնում է ապրանք զամբյուղում"""
#         product_id = str(product.id)
#
#         # Նոր բանալիի կառուցվածք՝ առանց size և colors
#         key = product_id
#
#         if key not in self.cart:
#             self.cart[key] = {
#                 'size': size,
#                 'colors': colors,
#                 'quantity': quantity,
#                 'price': str(price),
#                 'final_price': str(final_price) if final_price else None
#             }
#         else:
#             if override:
#                 self.cart[key]['quantity'] = quantity
#             else:
#                 self.cart[key]['quantity'] += quantity
#
#         self.save()
#
#     def save(self):
#         """Պահպանում է զամբյուղը session-ում"""
#         self.session[settings.CART_SESSION_ID] = self.cart
#         self.session.modified = True
#
#     def remove(self, product):
#         """Հեռացնում է ապրանքը զամբյուղից"""
#         product_id = str(product.id)
#         if product_id in self.cart:
#             del self.cart[product_id]
#             self.save()
#
#     def clear(self):
#         """Մաքրում է զամբյուղը"""
#         self.session.pop(settings.CART_SESSION_ID, None)
#         self.session.pop('coupon_code', None)
#         self.save()
#
#     def get_total_price(self):
#         return sum((Decimal(item.get('final_price') or item.get('price')) * item['quantity']) for item in self)
#
#     def get_discount(self):
#         """Վերադարձնում է զեղչի արժեքը"""
#         return self.discount  # Decimal վերադարձնել
#
#     def get_total_after_discount(self):
#         return self.get_total_price() - self.get_discount()
#
#     def get_shipping_cost(self):
#         """
#         Calculate the shipping cost based on conditions.
#         """
#         price_currency = self.request.GET.get('price_currency', 'USD')  # Default to 'USD' if not provided
#         total_after_discount = self.get_total_after_discount()
#
#         free_shipping_thresholds = {
#             "USD": 100,
#             "AMD": 40000,
#             "RUB": 10000
#         }
#
#         if price_currency in free_shipping_thresholds and total_after_discount > free_shipping_thresholds[
#             price_currency]:
#             return Decimal(0)
#         return Decimal(10)
#
#     def get_total_with_shipping(self):
#         return self.get_total_after_discount() + self.get_shipping_cost()
#
#     def apply_coupon(self, code):
#         """
#         Apply a coupon if valid, calculate discount, and disable it after use if it's one-time use.
#         """
#         try:
#             coupon = Coupon.objects.get(code=code)
#             if coupon.is_valid():
#                 self.coupon = coupon
#                 self.discount = self.get_total_price() * (coupon.discount / 100)
#                 self.session['coupon_code'] = coupon.code  # Պահպանում ենք session-ում
#
#                 if coupon.is_one_time_use:
#                     coupon.is_used = True
#                     coupon.save()
#             else:
#                 self.discount = Decimal(0)
#                 self.session.pop('coupon_code', None)  # Հեռացնում ենք կուպոնը
#         except Coupon.DoesNotExist:
#             self.discount = Decimal(0)
#             self.session.pop('coupon_code', None)
#
#         self.save()
#
#     def remove_coupon(self):
#         """
#         Remove the applied coupon.
#         """
#         self.coupon = None
#         self.discount = Decimal(0)
#         self.save()
#
#     def is_empty(self):
#         """
#         Check if the cart is empty.
#         """
#         return len(self.cart) == 0
#
#     def get_items(self):
#         return [(item.get('product'), item['quantity'], item['total_price']) for item in self]
#
#
