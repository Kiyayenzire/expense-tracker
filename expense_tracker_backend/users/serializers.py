


from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer used for returning user information
    """

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles user registration.
    """

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
        ]

    def validate(self, data):
        data["email"] = data["email"].lower().strip()
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Passwords do not match"}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        email = validated_data["email"]
        # Prevent duplicate registration attempts
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists"}
            )
        user = CustomUser.objects.create_user(
            username=email,  # username mirrors email
            email=email,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
            is_active=False  # must activate via email
        )

        return user


class EmailCheckSerializer(serializers.Serializer):
    """
    Ensures email is valid and not already registered.
    """

    email = serializers.EmailField()

    def validate_email(self, value):

        value = value.lower().strip()

        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already registered. Please login."
            )

        return value


