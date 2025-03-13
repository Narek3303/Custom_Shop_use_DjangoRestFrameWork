from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class OrderPermission(BasePermission):
    """
    Allow access to a given Order if the user is entitled to.
    Admins can access all orders.
    """

    def has_permission(self, request, view):
        # Ադմիններին տալիս ենք լիարժեք հասանելիություն
        if request.user.is_authenticated and request.user.is_staff:
            return True

        # Պարզ օգտատերերը պետք է լինեն մուտք գործած
        if view.many and request.customer.is_visitor:
            detail = _("Only signed in customers can view their list of orders.")
            raise PermissionDenied(detail=detail)

        return True

    def has_object_permission(self, request, view, order):
        # Ադմինը կարող է տեսնել բոլոր պատվերները
        if request.user.is_authenticated and request.user.is_staff:
            return True

        # Հասանելիություն տալ միայն սեփական պատվերներին
        if request.user.is_authenticated:
            return order.customer.pk == request.user.pk

        # Թույլատրել հասանելիություն, եթե կա ճիշտ `secret` գաղտնաբառ
        if order.secret and order.secret == view.kwargs.get('secret'):
            return True

        # Եթե ոչ մի պայման չի բավարարվում՝ մերժել հասանելիությունը
        detail = _("This order does not belong to you.")
        raise PermissionDenied(detail=detail)
