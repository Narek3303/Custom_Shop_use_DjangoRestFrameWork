from rest_framework import serializers
from .models import Post
from django.contrib.auth import get_user_model




class PostListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'created', 'title', 'image']



class PostDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'




class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username')




