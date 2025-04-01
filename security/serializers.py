from rest_framework import serializers
from .models import AllowedIP, BlockedIP, IPAccessLog, SuspiciousIPPattern


class AllowedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedIP
        fields = '__all__'
        extra_kwargs = {
            'expires_at': {'required': False},
            'description': {'required': False},
        }

    def validate(self, data):
        if not data.get('ip_address') and not data.get('ip_network'):
            raise serializers.ValidationError("Պետք է նշվի կամ IP հասցե կամ IP ցանց:")
        if data.get('ip_address') and data.get('ip_network'):
            raise serializers.ValidationError("Չի կարելի նշել և՛ IP հասցե, և՛ IP ցանց:")
        return data


class BlockedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedIP
        fields = '__all__'

    def validate_ip_address(self, value):
        if AllowedIP.objects.filter(ip_address=value).exists():
            raise serializers.ValidationError("Այս IP հասցեն արդեն թույլատրվածների ցանկում է:")
        return value


class IPAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPAccessLog
        fields = '__all__'
        read_only_fields = ['accessed_at']


class SuspiciousIPPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuspiciousIPPattern
        fields = '__all__'

    def validate_pattern(self, value):
        if SuspiciousIPPattern.objects.filter(pattern=value).exists():
            raise serializers.ValidationError("Այսօրինակ նմուշ արդեն գոյություն ունի:")
        return value
