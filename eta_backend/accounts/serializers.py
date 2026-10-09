from rest_framework import serializers
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.socialaccount.models import SocialAccount

User = get_user_model()


class EmailVerificationRegisterSerializer(RegisterSerializer):
    def save(self, request):
        user = super().save(request)
        user.is_active = False
        user.save(update_fields=['is_active'])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    has_usable_password = serializers.SerializerMethodField()
    social_providers = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'monthly_income',
            'role',
            'profile_picture',
            'profile_picture_url',
            'has_usable_password',
            'social_providers',
            'email_verified',
        ]
        read_only_fields = [
            'id', 'username', 'email', 'role',
            'has_usable_password', 'social_providers',
        ]

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()

    def get_email_verified(self, obj):
        return EmailAddress.objects.filter(
            user=obj,
            email__iexact=obj.email,
            verified=True,
        ).exists()

    def get_social_providers(self, obj):
        return sorted(
            set(SocialAccount.objects.filter(user=obj).values_list('provider', flat=True))
        )

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        if not obj.profile_picture:
            return None
        if request is not None:
            return request.build_absolute_uri(obj.profile_picture.url)
        return obj.profile_picture.url

    def update(self, instance, validated_data):
        profile_picture = validated_data.get('profile_picture')
        if profile_picture is not None:
            instance.profile_picture = profile_picture
        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            instance.last_name = validated_data['last_name']
        if 'phone_number' in validated_data:
            instance.phone_number = validated_data['phone_number']
        if 'monthly_income' in validated_data:
            instance.monthly_income = validated_data['monthly_income']
        instance.save()
        return instance
