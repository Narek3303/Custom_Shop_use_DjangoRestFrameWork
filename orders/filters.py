from django_filters import rest_framework as filters
from .models import Order, OrderStatus

class OrderFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=OrderStatus.choices, label="Order Status")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr='gte', label="Date From")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr='lte', label="Date To")

    class Meta:
        model = Order
        fields = ['status', 'date_from', 'date_to']
