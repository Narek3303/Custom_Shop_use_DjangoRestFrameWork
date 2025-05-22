from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.http import request
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK
from social_django.models import UserSocialAuth
from django.shortcuts import render


from google.auth.transport.requests import Request
from google.oauth2 import id_token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from .serializers import UserTokenCheckSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import MethodNotAllowed
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from .models import UserProfile
from .serializers import UserProfileSerializer



@api_view(['POST'])
def verify_google_token(request):
    token = request.data.get('token')

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, Request(), settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID)

        # Now you have the user's Google account information
        user_email = idinfo.get('email')
        # You can either create a user or authenticate the existing one
        return Response({"message": "User authenticated", "email": user_email}, status=status.HTTP_200_OK)

    except ValueError:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)



User = get_user_model()

@receiver(post_save, sender=UserSocialAuth)
def verify_social_user(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        if not user.is_verified:  # Եթե դեռ չվավերացված է
            user.is_verified = True
            user.save()



class UserTokenCheckView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserTokenCheckSerializer




    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        token = serializer.data['token']
        tokens = Token.objects.all()
        content = {'Not': 'Token chka'}
        if token in tokens:
            content = {'OK': 'Token ka'}
            return Response(content, HTTP_200_OK)
        return Response(content, status.HTTP_404_NOT_FOUND)











class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission that allows users to edit only their own profile,
    while admin users can view and edit all profiles.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read-only access for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user == obj.user or request.user.is_staff


class UserProfileViewSet(ModelViewSet):
    """User Profile API Endpoint"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']  # Allow POST for profile creation

    def get_queryset(self):
        """Optimized queryset that selects related user and applies filtering"""
        queryset = UserProfile.objects.select_related('user')
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Ստեղծում է պրոֆիլ, եթե այն դեռ չի գոյություն ունենում"""
        user = self.request.user
        # Եթե օգտատերը արդեն ունի պրոֆիլ, ապա կանխում ենք ստեղծումը
        if hasattr(user, 'profile'):
            raise MethodNotAllowed('POST', detail="Օգտատեր արդեն ունի պրոֆիլ.")
        # Հիմա պահում ենք պրոֆիլը առանց `user` արգումենտի կրկին փոխանցելու
        serializer.save()

    def perform_update(self, serializer):
        """Handle avatar updates and cleanup of old files"""
        instance = serializer.instance
        new_avatar = serializer.validated_data.get('avatar')

        # Delete old avatar if a new one is provided
        if new_avatar and instance.avatar:
            instance.avatar.delete(save=False)

        serializer.save()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Endpoint for current user's profile.
        GET: Retrieve current user's profile
        PUT/PATCH: Update current user's profile
        """
        profile = get_object_or_404(UserProfile, user=request.user)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        # Handle updates
        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def deactivate(self, request):
        """
        Deactivate the current user's account.
        POST: Sets user.is_active = False
        """
        user = request.user
        if not user.is_active:
            return Response(
                {"detail": "Account is already deactivated."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = False
        user.save()
        return Response(
            {"detail": "Account successfully deactivated."},
            status=status.HTTP_200_OK
        )





