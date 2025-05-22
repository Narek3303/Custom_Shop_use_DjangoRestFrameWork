from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
from django.core.validators import RegexValidator
import re
import regex





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
            'first_name',
            'last_name',
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


    def validate_first_name(self, value):
        value = value.strip().title()

        if not regex.match(r"^[\p{L}ʼ\-]+$", value):
            raise serializers.ValidationError(_("Անունը պետք է պարունակի միայն այբբենական տառեր և հնարավոր է մեկ շտրիխ (') կամ գծիկ (-)։"))

        if len(value) < 2:
            raise serializers.ValidationError(_("Անունը պետք է լինի առնվազն 2 նիշ երկար։"))

        if len(value) > 50:
            raise serializers.ValidationError(_("Անունը չպետք է գերազանցի 50 նիշ։"))

        return value




    def validate_last_name(self, value):
        value = value.strip().title()

        if not regex.match(r"^[\p{L}ʼ\-]+$", value):
            raise serializers.ValidationError(_("Ազգանունը պետք է պարունակի միայն այբբենական տառեր և հնարավոր է մեկ շտրիխ (') կամ գծիկ (-)։"))

        if len(value) < 2:
            raise serializers.ValidationError(_("Ազգանունը պետք է պարունակի միայն այբբենական տառեր և հնարավոր է մեկ շտրիխ (') կամ գծիկ (-)։"))

        if len(value) > 50:
            raise serializers.ValidationError(_("Ազգանունը չպետք է գերազանցի 50 նիշ։"))

        return value


    def validate_phone_number(self, value):
        phone_regex = RegexValidator(
            regex=r"^\+?1?\d{9,15}$",
            message=_("Հեռախոսահամարը պետք է լինի միջազգային ֆորմատով՝ օրինակ՝ +37491234567։")
        )
        phone_regex(value)
        return value


    def validate_postal_code(self, value):

        value = value.replace(' ', '')

        if not value.isalnum():
            raise serializers.ValidationError(_("Փոստային կոդը պետք է պարունակի միայն թվեր և տառեր։"))


        if len(value) < 3 or len(value) > 10:
            raise serializers.ValidationError(_("Փոստային կոդը պետք է ունենա 3-ից 10 նիշ։"))

        if not re.match(r"^[A-Za-z0-9\-]{3,10}$", value):
            raise serializers.ValidationError(_("Փոստային կոդը պետք է լինի միայն տառեր, թվեր կամ գիծ (նախադասական է)։"))

        return value

    def validate_birth_date(self, value):

        today = date.today()
        min_age = 18
        min_birth_date = today - timedelta(days=min_age * 365)

        if value >= today:
            raise serializers.ValidationError(_("Ծննդյան ամսաթիվը չի կարող լինել ապագայում։"))

        if value > min_birth_date:
            raise serializers.ValidationError(_("Դուք պետք է լինեք առնվազն 18 տարեկան։"))

        if value.year < 1900:
            raise serializers.ValidationError(_("Խնդրում ենք մուտքագրել վավեր ծննդյան տարեթիվ (1900-ից հետո)։"))


        return value


    def validate(self, data):
        instance = getattr(self, 'instance', None)
        if instance:
            for field in ['first_name', 'last_name', 'phone_number', 'address', 'city', 'country', 'postal_code', 'birth_date']:
                if field in data and data[field] in [None, '', []]:
                    raise serializers.ValidationError({field: _("Այս դաշտը չի կարող դատարկ լինել, քանի որ այն արդեն լրացված է։")})
        return data
