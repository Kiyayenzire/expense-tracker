from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
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
    email = serializers.EmailField(required=False)
    profile_picture_url = serializers.SerializerMethodField()
    has_usable_password = serializers.SerializerMethodField()
    social_providers = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    pending_email = serializers.SerializerMethodField()
    email_change_deadline = serializers.SerializerMethodField()
    email_change_days_remaining = serializers.SerializerMethodField()
    email_change_pending = serializers.SerializerMethodField()
    email_update_required = serializers.SerializerMethodField()

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
            'pending_email',
            'email_change_deadline',
            'email_change_days_remaining',
            'email_change_pending',
            'email_update_required',
        ]
        read_only_fields = [
            'id', 'username', 'role',
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

    def get_pending_email(self, obj):
        if obj.email_change_requested_at is None:
            return None
        address = EmailAddress.objects.filter(
            user=obj,
            verified=False,
        ).exclude(email__iexact=obj.email).order_by('-id').first()
        return address.email if address else None

    def get_email_change_pending(self, obj):
        return self.get_pending_email(obj) is not None

    def get_email_update_required(self, obj):
        return obj.email_change_requested_at is not None

    def get_email_change_deadline(self, obj):
        deadline = obj.email_change_deadline
        return deadline

    def get_email_change_days_remaining(self, obj):
        deadline = obj.email_change_deadline
        if deadline is None:
            return None
        seconds_remaining = (deadline - timezone.now()).total_seconds()
        return max(0, int((seconds_remaining + 86399) // 86400))

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

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if normalized_email == self.instance.email.lower():
            return normalized_email
        if User.objects.filter(email__iexact=normalized_email).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This email address is already in use.')
        if EmailAddress.objects.filter(email__iexact=normalized_email).exclude(user=self.instance).exists():
            raise serializers.ValidationError('This email address is already in use.')
        return normalized_email

    def update(self, instance, validated_data):
        new_email = validated_data.pop('email', None)
        email_changed = bool(new_email and new_email.lower() != instance.email.lower())
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
        with transaction.atomic():
            instance.save()
            if email_changed:
                address = EmailAddress.objects.filter(
                    user=instance,
                    email__iexact=new_email,
                ).first()
                is_existing_pending_email = bool(
                    address
                    and not address.verified
                    and instance.email_change_requested_at is not None
                    and address.email.lower() != instance.email.lower()
                )
                if not is_existing_pending_email:
                    if address and address.verified:
                        EmailAddress.objects.filter(user=instance, primary=True).exclude(pk=address.pk).update(primary=False)
                        address.primary = True
                        address.save(update_fields=['primary'])
                        instance.email = new_email
                        instance.email_change_requested_at = None
                        instance.email_change_deactivated_at = None
                        instance.email_change_original_email = ''
                        instance.save(update_fields=[
                            'email',
                            'email_change_requested_at',
                            'email_change_deactivated_at',
                            'email_change_original_email',
                        ])
                    else:
                        if address is None:
                            address = EmailAddress.objects.create(
                                user=instance,
                                email=new_email,
                                primary=False,
                                verified=False,
                            )
                        EmailAddress.objects.filter(
                            user=instance,
                            verified=False,
                        ).exclude(pk=address.pk).delete()
                        if instance.email_change_requested_at is None:
                            instance.email_change_original_email = instance.email
                        instance.email_change_requested_at = timezone.now()
                        instance.email_change_deactivated_at = None
                        instance.save(update_fields=[
                            'email_change_requested_at',
                            'email_change_deactivated_at',
                            'email_change_original_email',
                        ])
                        self.context['email_change_address_id'] = address.pk
        return instance
