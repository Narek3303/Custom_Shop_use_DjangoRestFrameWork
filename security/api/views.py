from rest_framework import viewsets, permissions
from rest_framework.response import Response
from security.models import AllowedIP, BlockedIP
from security.serializers import AllowedIPSerializer, BlockedIPSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import DjangoModelPermissions

class AllowedIPViewSet(viewsets.ModelViewSet):
    queryset = AllowedIP.objects.only("ip_address", "is_active", "ip_network")  # Օպտիմալացում
    serializer_class = AllowedIPSerializer
    permission_classes = [permissions.IsAdminUser, DjangoModelPermissions]  # Թույլտվությունների բարելավում
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'ip_address', 'ip_network']

class BlockedIPViewSet(viewsets.ModelViewSet):
    queryset = BlockedIP.objects.only("ip_address", "is_active", "reason")  # Օպտիմալացում
    serializer_class = BlockedIPSerializer
    permission_classes = [permissions.IsAdminUser, DjangoModelPermissions]  # Թույլտվությունների բարելավում
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'ip_address', 'reason']  # `reason` դաշտի ավելացում
