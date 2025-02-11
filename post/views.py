from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from .models import Post
from .serializers import PostListSerializer, PostDetailSerializer, UserSerializer
from rest_framework import generics, permissions
from .permissions import IsAuthorOrReadOnly
from rest_framework import viewsets



class PostListAPIView(generics.ListAPIView):
    queryset = Post.published.all()
    serializer_class = PostListSerializer



class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Post.published.all()
    serializer_class = PostDetailSerializer



class UserList(generics.ListCreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer




# class PostViewSet(viewsets.ModelViewSet):
#     permission_classes = (IsAuthorOrReadOnly,)
#     queryset = Post.objects.all()
#     serializer_class = PostListSerializer
#
#
#
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = get_user_model().objects.all()
#     serializer_class = PostListSerializer