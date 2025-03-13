from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework import generics, mixins
from rest_framework.exceptions import NotFound, MethodNotAllowed, PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from shop.rest.money import JSONRenderer
from shop.rest.renderers import CMSPageRenderer
from shop.serializers.order import OrderListSerializer, OrderDetailSerializer
from shop.models.order import OrderModel
from .permissions import OrderPermission


class OrderPagination(LimitOffsetPagination):
    default_limit = 15
    template = 'shop/templatetags/paginator.html'





class OrderView(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    """
    Base View class to handle order listing, retrieval, and updates for the current user.
    """
    renderer_classes = [CMSPageRenderer, JSONRenderer, BrowsableAPIRenderer]
    list_serializer_class = OrderListSerializer
    detail_serializer_class = OrderDetailSerializer
    pagination_class = OrderPagination
    permission_classes = [OrderPermission]
    lookup_field = lookup_url_kwarg = 'slug'
    many = True
    last_order_lapse = timezone.timedelta(minutes=15)

    def get_queryset(self):
        """
        Filter orders based on the current user, excluding visitors.
        """
        queryset = OrderModel.objects.all()
        if not self.request.customer.is_visitor:
            queryset = queryset.filter(customer=self.request.customer).order_by('-updated_at')
        return queryset

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the view type.
        """
        return self.list_serializer_class if self.many else self.detail_serializer_class

    def get_renderer_context(self):
        """
        Customize the renderer context for the template view.
        """
        renderer_context = super().get_renderer_context()
        if self.request.accepted_renderer.format == 'html':
            renderer_context.update(many=self.many)
            if not self.many:
                # Add extra breadcrumb information to display order number
                renderer_context.update(
                    is_last_order=self.is_last(),
                    extra_ance=self.get_object().get_number(),
                )
        return renderer_context

    def is_last(self):
        """
        Returns `True` if the given order is considered the last order for the customer.
        Used to distinguish between a "thank you" and a normal detail view.
        """
        assert not self.many, "This method can be called for detail views only"
        lapse = timezone.now() - self.last_order_lapse
        current_order = self.get_object()
        last_order = self.get_queryset().first()
        return current_order.id == last_order.id and current_order.created_at > lapse

    @property
    def allowed_methods(self):
        """
        Restrict "POST" method only for the detail view.
        """
        allowed_methods = super().allowed_methods
        if self.many:
            allowed_methods.remove('POST')
        return allowed_methods

    @never_cache
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for both list and detail views.
        """
        if self.many:
            return self.list(request, *args, **kwargs)
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for order detail views.
        """
        if self.many:
            raise MethodNotAllowed("POST method is not allowed on Order List View.")
        self.update(request, *args, **kwargs)
        return self.retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Return a list of orders for the current user.
        """
        try:
            return super().list(request, *args, **kwargs)
        except OrderModel.DoesNotExist:
            raise NotFound("No orders have been found for the current user.")

    def retrieve(self, request, *args, **kwargs):
        """
        Return details of a specific order.
        """
        try:
            return super().retrieve(request, *args, **kwargs)
        except OrderModel.DoesNotExist:
            raise NotFound("No order has been found for the current user.")

    def create(self, request, *args, **kwargs):
        """
        Allow authenticated users to create a new order.
        Only available if the customer is not a visitor.
        """
        if request.customer.is_visitor:
            raise PermissionDenied(_("You need to be signed in to create an order."))
        return super().create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Allow authenticated users to delete their order if they are the customer.
        """
        order = self.get_object()
        if order.customer.pk != request.user.pk:
            raise PermissionDenied(_("You are not authorized to delete this order."))
        order.delete()
        return Response({"detail": _("Order deleted successfully.")}, status=status.HTTP_204_NO_CONTENT)

