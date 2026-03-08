

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib.auth import authenticate, get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


from users.models import CustomUser
from users.serializers import (
    EmailCheckSerializer,
    RegisterSerializer,
    UserSerializer,
)


User = get_user_model()



class EmailCheckView(APIView):
    """
    Step 1: verify email is valid and not registered
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailCheckSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {"message": "Email is valid. Continue registration."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """
    Register a new user.

    Process:
    1. User submits email + details
    2. Account created but inactive
    3. Activation email sent
    """

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            activation_link = f"http://localhost:5173/activate/{user.activation_token}"

            # Send activation email
            send_mail(
                subject="Activate your account",
                message=f"""
Welcome!

Please activate your account using the link below:

{activation_link}

If you did not request this account, ignore this email.
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {
                    "message": "Account created. Please check your email to activate it."
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateUserView(APIView):
    """
    Activates user account after email verification.
    """

    permission_classes = [AllowAny]

    def get(self, request, token):

        try:

            user = CustomUser.objects.get(activation_token=token)

            # Prevent activating already active accounts
            if user.is_active:
                return redirect("http://localhost:5173/login")

            user.is_active = True

            # Clear token so it cannot be reused
            user.activation_token = None

            user.save()

            # Redirect to login page
            return redirect("http://localhost:5173/login")

        except CustomUser.DoesNotExist:

            return Response(
                {"error": "Invalid activation token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(APIView):
    """
    Authenticate user and return JWT tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email", "").lower()
        password = request.data.get("password", "")

        # authenticate returns None if invalid credentials or inactive user
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials or account inactive."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # generate JWT
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class CurrentUserView(APIView):
    """
    Returns the currently authenticated user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)



