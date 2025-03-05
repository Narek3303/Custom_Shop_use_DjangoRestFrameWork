from rest_framework import serializers


class UserTokenCheckSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)

