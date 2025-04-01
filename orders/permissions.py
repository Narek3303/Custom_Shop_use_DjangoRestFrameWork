from rest_framework import permissions
from django.contrib.auth.models import Permission
from .models import Order, OrderStatusLog

class IsOwner(permissions.BasePermission):
    """
    Only allows access to the owner of the object
    """
    message = "You must be the owner of this object."

    def has_object_permission(self, request, view, obj):
        # Works for Order, OrderItem, ShippingAddress, etc.
        return obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access to owners or admin users
    """
    message = "You must be the owner or an admin."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to all users, but write access only to admins
    """
    message = "You must be an admin to perform this action."

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_staff
        )


class CanCreateOrder(permissions.BasePermission):
    """
    Checks if user can create an order
    """
    message = "You don't have permission to create orders."

    def has_permission(self, request, view):
        # Example: Check if user has a verified account
        return (
            request.user.is_authenticated and
            request.user.is_active and
            (hasattr(request.user, 'is_verified') and request.user.is_verified)
        )


class CanModifyOrder(permissions.BasePermission):
    """
    Checks if order can be modified (only in PENDING state)
    """
    message = "This order can no longer be modified."

    def has_object_permission(self, request, view, obj):
        return (
            obj.status == Order.OrderStatus.PENDING and
            (obj.user == request.user or request.user.is_staff)
        )


class CanCancelOrder(permissions.BasePermission):
    """
    Checks if order can be cancelled
    """
    message = "This order can no longer be cancelled."

    def has_object_permission(self, request, view, obj):
        cancellable_statuses = [
            Order.OrderStatus.PENDING,
            Order.OrderStatus.PROCESSING
        ]
        return (
            obj.status in cancellable_statuses and
            (obj.user == request.user or request.user.is_staff)
        )


class CanViewOrderHistory(permissions.BasePermission):
    """
    Checks if user can view order history
    """
    message = "You don't have permission to view order history."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.has_perm('orders.view_orderhistory') or
             request.user.is_staff)
        )


class HasOrderPermission(permissions.BasePermission):
    """
    Checks for specific order-related permissions
    """
    def __init__(self, perm):
        self.perm = perm
        self.message = f"You don't have the '{perm}' permission."

    def has_permission(self, request, view):
        return request.user.has_perm(self.perm)


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Special permission that works with OrderStatusLog
    """
    message = "You must be the order owner or an admin."

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, OrderStatusLog):
            return obj.order.user == request.user or request.user.is_staff
        return obj.user == request.user or request.user.is_staff


class CanExportOrders(permissions.BasePermission):
    """
    Permission for exporting order data
    """
    message = "You don't have permission to export orders."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_staff or
             request.user.has_perm('orders.export_orders'))
        )


class PaymentPermission(permissions.BasePermission):
    """
    Base permission for payment-related actions
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_active and
            hasattr(request.user, 'payment_methods')
        )


class CanProcessRefund(permissions.BasePermission):
    """
    Checks if user can process refunds
    """
    message = "You don't have permission to process refunds."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_staff or
             request.user.has_perm('orders.process_refund'))
        )


class ShippingPermission(permissions.BasePermission):
    """
    Base permission for shipping-related actions
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_staff or
             request.user.has_perm('orders.manage_shipping'))
        )


class CustomPermissionLogic:
    """
    Utility class for complex permission logic
    """
    @staticmethod
    def can_view_sensitive_data(user, order):
        """
        Checks if user can view sensitive order data
        """
        return (
            user.is_staff or
            order.user == user or
            user.has_perm('orders.view_sensitive_data')
        )

    @staticmethod
    def can_edit_order_items(user, order):
        """
        Checks if user can edit order items
        """
        return (
            order.status == Order.OrderStatus.PENDING and
            (order.user == user or user.is_staff or
             user.has_perm('orders.edit_order_items'))
        )


