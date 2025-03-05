from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.http import request
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK
from social_django.models import UserSocialAuth
from django.shortcuts import render

import google.auth
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
