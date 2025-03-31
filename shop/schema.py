import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene import ObjectType, String, Float, Int, List, Field
from graphene_django.forms.mutation import DjangoModelFormMutation
from django.db.models import Count, Sum, F
from orders.models import Order, OrderStatus
from .models import Product
from .forms import OrderForm
from django.db.models import Q


# 📌 Պատվերի տեսակ (OrderType)
class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        filter_fields = ['status', 'created_at', 'total_price',
                         'user']  # Ֆիլտրեր՝ ըստ կարգավիճակի, ստեղծման ամսաթվի, գնի և օգտատիրոջ
        interfaces = (graphene.relay.Node,)  # Relay՝ էջավորման համար


# 📌 Ապրանքի տեսակ (ProductType)
class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        filter_fields = ['name', 'category', 'price',
                         'rating']  # Ֆիլտրեր՝ ըստ ապրանքի անվան, կատեգորիայի, գնի և վարկանիշի
        interfaces = (graphene.relay.Node,)  # Relay՝ էջավորման համար


# 📌 Հարցումներ (Queries)
class Query(graphene.ObjectType):
    # Ամբողջ պատվերները՝ ֆիլտրերով և որոնմամբ
    all_orders = DjangoFilterConnectionField(OrderType, status=graphene.String(), created_at=graphene.String(),
                                             min_price=graphene.Float(), max_price=graphene.Float(),
                                             user_name=graphene.String())

    # Ամբողջ ապրանքները՝ ֆիլտրերով, որոնմամբ և դասավորությամբ
    all_products = DjangoFilterConnectionField(ProductType, name=graphene.String(), category=graphene.String(),
                                               min_price=graphene.Float(), max_price=graphene.Float(),
                                               rating=graphene.Int())

    # Ապրանքներ ըստ վաճառքի քանակի
    top_selling_products = graphene.List(ProductType, limit=graphene.Int(default_value=5))

    # Ապրանքներ ըստ ընդհանուր վաճառքի արժեքի
    popular_products = graphene.List(ProductType, limit=graphene.Int(default_value=5))

    # Գրանցված ապրանքներ՝ օգտագործողի և վարկանիշի համաձայն
    filtered_products = graphene.List(ProductType, min_rating=graphene.Int(), max_price=graphene.Float())

    # Հարցերի լուծումներ (Resolvers)
    def resolve_all_orders(self, info, status=None, created_at=None, min_price=None, max_price=None, user_name=None):
        queryset = Order.objects.all()
        if status:
            queryset = queryset.filter(status=status)
        if created_at:
            queryset = queryset.filter(created_at__date=created_at)
        if min_price is not None:
            queryset = queryset.filter(total_price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(total_price__lte=max_price)
        if user_name:
            queryset = queryset.filter(user__username__icontains=user_name)
        return queryset

    def resolve_all_products(self, info, name=None, category=None, min_price=None, max_price=None, rating=None):
        queryset = Product.objects.all()
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category__icontains=category)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if rating is not None:
            queryset = queryset.filter(rating__gte=rating)
        return queryset

    def resolve_top_selling_products(self, info, limit):
        # Վաճառված ապրանքներ՝ ըստ քանակի
        return Product.objects.annotate(sold_quantity=Count('orderitem__product')) \
                   .order_by('-sold_quantity')[:limit]

    def resolve_popular_products(self, info, limit):
        # Վաճառված ապրանքներ՝ ըստ ընդհանուր վաճառքի արժեքի
        return Product.objects.annotate(total_sales_value=Sum(F('orderitem__price') * F('orderitem__quantity'))) \
                   .order_by('-total_sales_value')[:limit]

    def resolve_filtered_products(self, info, min_rating=None, max_price=None):
        queryset = Product.objects.all()
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset


# 📌 Պատվերի ստեղծման մուտացիա
class CreateOrderMutation(DjangoModelFormMutation):
    class Meta:
        form_class = OrderForm  # فرضاً استفاده از فرم Django


# 📌 Մուտացիաներ
class Mutation(graphene.ObjectType):
    create_order = CreateOrderMutation.Field()  # Պատվեր ստեղծելու մուտացիա


# 📌 Գրաֆեն Սքեմա
schema = graphene.Schema(query=Query, mutation=Mutation)
