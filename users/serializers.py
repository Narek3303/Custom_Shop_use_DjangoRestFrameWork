from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile




class UserTokenCheckSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)



User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user_email",
            "phone_number",
            "address",
            "city",
            "country",
            "postal_code",
            "birth_date",
            "avatar",
            "avatar_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_email", "created_at", "updated_at", "avatar_url"]
        extra_kwargs = {
            'avatar': {'write_only': True}
        }

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def create(self, validated_data):
        # Վերցնում ենք օգտագործողի տվյալները `request`-ից
        user = self.context['request'].user  # Ստանում ենք օգտագործողին `request`-ի կոնտեքստից
        validated_data['user'] = user  # Վերադարձնում ենք `user`-ը `validated_data`-ում
        return UserProfile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update profile with proper avatar handling"""
        avatar = validated_data.get('avatar')

        # Delete old avatar if new one is provided
        if avatar and instance.avatar:
            instance.avatar.delete(save=False)

        return super().update(instance, validated_data)
