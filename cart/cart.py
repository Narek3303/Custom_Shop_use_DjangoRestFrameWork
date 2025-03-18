from decimal import Decimal


from django.conf import settings
from shop.models import Product
from coupon.models import Coupon


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID, {})
        self.cart = cart
        self.coupon = None
        self.discount = Decimal(0)
        self.request = request

        # Վերականգնում ենք կուպոնը session-ից
        coupon_code = self.session.get('coupon_code')
        if coupon_code:
            try:
                self.coupon = Coupon.objects.get(code=coupon_code)
                self.discount = self.get_total_price() * (self.coupon.discount / 100)
            except Coupon.DoesNotExist:
                self.coupon = None
                self.discount = Decimal(0)

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        cart = self.cart.copy()  # Խուսափում ենք ուղիղ փոփոխումից

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item.get('final_price', item['price']))  # Եթե final_price կա, օգտագործում ենք այն
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def add(self, product, color, size_id, price, final_price, quantity=1, override=False,):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            # Ստեղծում ենք նոր արտադրանք
            self.cart[product_id] = {
                'size_id': size_id,
                'color': color,
                'quantity': quantity,
                'price': price,
                'final_price': final_price
            }
        else:
            # Ավելացնում ենք քանակը կամ փոխում այն
            if override:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):

        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        # Remove cart from session if it exists
        self.session.pop(settings.CART_SESSION_ID, None)
        self.session.pop('coupon_code', None)
        self.save()

    def get_total_price(self):
        total = Decimal(0)

        for item in self.cart.values():
            price = Decimal(item.get('final_price', item['price']))  # Եթե final_price կա, օգտագործում ենք այն
            total += price * item['quantity']

        return total

    def get_discount(self):
        """
        Calculate the discount (if any).
        """
        return self.discount

    def get_total_after_discount(self):
        """
        Return total after applying the discount.
        """
        total = self.get_total_price()
        return total - self.get_discount()

    def get_shipping_cost(self):
        """
        Calculate the shipping cost based on conditions.
        """
        price_currency = self.request.GET.get('price_currency', 'USD')  # Default to 'USD' if not provided
        total_after_discount = self.get_total_after_discount()

        free_shipping_thresholds = {
            "USD": 100,
            "AMD": 40000,
            "RUB": 10000
        }

        if price_currency in free_shipping_thresholds and total_after_discount > free_shipping_thresholds[
            price_currency]:
            return Decimal(0)

        return Decimal(10)

    def get_total_with_shipping(self):
        return self.get_total_after_discount() + self.get_shipping_cost()

    def apply_coupon(self, code):
        """
        Apply a coupon if valid, calculate discount, and disable it after use if it's one-time use.
        """
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_valid():
                self.coupon = coupon
                self.discount = self.get_total_price() * (coupon.discount / 100)
                self.session['coupon_code'] = coupon.code  # Պահպանում ենք session-ում

                if coupon.is_one_time_use:
                    coupon.is_used = True
                    coupon.save()
            else:
                self.discount = Decimal(0)
                self.session.pop('coupon_code', None)  # Հեռացնում ենք կուպոնը
        except Coupon.DoesNotExist:
            self.discount = Decimal(0)
            self.session.pop('coupon_code', None)

        self.save()

    def remove_coupon(self):
        """
        Remove the applied coupon.
        """
        self.coupon = None
        self.discount = Decimal(0)
        self.save()

    def is_empty(self):
        """
        Check if the cart is empty.
        """
        return len(self.cart) == 0

    def get_items(self):
        return [(item.get('product'), item['quantity'], item['total_price']) for item in self]


