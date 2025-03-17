from decimal import Decimal


from django.conf import settings
from shop.models import Product
from coupon.models import Coupon


class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session if none exists
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
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

    def add(self, product, color, size, quantity=1, override=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            # Ստեղծում ենք նոր արտադրանք
            self.cart[product_id] = {
                'size': size,
                'color': color,
                'quantity': quantity,
                'price': Decimal(product.price),  # Ստանում ենք թվային արժեք
                'final_price': Decimal(product.final_price) if product.final_price else Decimal(product.price)
                # Ստուգում ենք final_price
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
        # Remove cart from session
        del self.session[settings.CART_SESSION_ID]
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

    def get_shipping_cost(self, request):
        """
        Calculate the shipping cost based on conditions.
        """
        price_currency = request.GET.get('price_currency', 'USD')  # Default to 'USD' if not provided
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
        """
        Return the total price including shipping costs.
        """
        return self.get_total_after_discount() + self.get_shipping_cost()

    def apply_coupon(self, code):
        """
        Apply a coupon if valid, calculate discount, and disable it after use if it's one-time use.
        """
        try:
            coupon = Coupon.objects.get(code=code)

            # Ստուգում ենք կուպոնի վավերությունը
            if coupon.is_valid():
                self.coupon = coupon

                # Հաշվում ենք զեղչը
                self.discount = self.get_total_price() * (coupon.discount / 100)

                # Հաշվարկելուց հետո կուպոնը պետք է լինի մեկ անգամ օգտագործվող
                if coupon.is_one_time_use:  # Գտնում ենք կուպոնի դաշտը
                    coupon.is_used = True  # Կուպոնն արդեն օգտագործվել է
                    coupon.save()  # Պահպանում ենք փոփոխությունը
            else:
                self.discount = Decimal(0)
        except Coupon.DoesNotExist:
            self.discount = Decimal(0)

        self.save()  # Պահպանում ենք զեղչը և կուպոնն

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
        """
        Get a list of all the items in the cart.
        """
        return [(item['product'], item['quantity'], item['total_price']) for item in self.cart.values()]

