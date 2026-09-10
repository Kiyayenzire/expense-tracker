from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

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
        ]
        read_only_fields = ['id', 'username', 'email', 'role']

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
