"""
Custom password reset and account management views for the accounts app.
"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import UserProfileSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def custom_login(request):
    """Authenticate a user and cancel any pending account-deletion request on successful login."""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({'detail': 'Username/email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(username__iexact=username).first() or User.objects.filter(email__iexact=username).first()
    if not user:
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

    auth_user = authenticate(request, username=user.username, password=password)
    if not auth_user:
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

    django_login(request, auth_user)
    token, _ = Token.objects.get_or_create(user=auth_user)
    profile = UserProfileSerializer(auth_user).data

    if auth_user.is_account_deletion_pending:
        auth_user.cancel_account_deletion()
        return Response({
            'key': token.key,
            'detail': 'You logged in again, so your pending account-deletion request was cancelled.',
            'cancelled_account_deletion': True,
            'user': profile,
        }, status=status.HTTP_200_OK)

    return Response({'key': token.key, 'user': profile}, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_details(request):
    """Return and update the authenticated user profile, including optional avatar image."""
    user = request.user

    if request.method == 'GET':
        return Response(UserProfileSerializer(user, context={'request': request}).data)

    serializer = UserProfileSerializer(user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(UserProfileSerializer(user, context={'request': request}).data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_account_deletion(request):
    """Request a delayed account deletion after the user confirms their current password."""
    password = request.data.get('password', '')
    if not password:
        return Response({'detail': 'Your current password is required to confirm account deletion.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    try:
        user.request_account_deletion(password)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'detail': 'Account deletion requested. Your account will be permanently deleted after 31 days unless you log in again, which cancels the request.',
        'account_deletion_requested_at': user.account_deletion_requested_at,
        'pending_deletion': True,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def custom_password_reset_request(request):
    """
    Request a password reset link via email.
    Expects: {'email': 'user@example.com'}
    """
    email = request.data.get('email', '').strip()
    
    if not email:
        return Response(
            {'detail': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # For security, don't reveal if email exists
        return Response(
            {'detail': 'If an account with this email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK
        )
    
    # Generate reset token and UID
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Build reset link
    reset_link = f"{settings.FRONTEND_URL}/#/reset-password/{uid}/{token}"
    
    # Send email
    subject = '[Expense Tracker] Password Reset Request'
    message = f"""
Hello {user.username},

You requested a password reset. Click the link below to reset your password:

{reset_link}

This link expires in 24 hours. If you didn't request this, ignore this email.

Best regards,
Expense Tracker Team
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return Response(
            {'detail': 'If an account with this email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'detail': f'Error sending reset email: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def custom_password_reset_confirm(request):
    """
    Confirm password reset with token and new password.
    Expects: {'uid': 'base64_uid', 'token': 'reset_token', 'new_password': 'password'}
    """
    uid = request.data.get('uid', '').strip()
    token = request.data.get('token', '').strip()
    new_password = request.data.get('new_password', '').strip()
    
    if not all([uid, token, new_password]):
        return Response(
            {'detail': 'UID, token, and new password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'detail': 'Password must be at least 8 characters long.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, User.DoesNotExist):
        return Response(
            {'detail': 'Invalid reset link.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate token
    if not default_token_generator.check_token(user, token):
        return Response(
            {'detail': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response(
        {'detail': 'Password has been reset successfully.'},
        status=status.HTTP_200_OK
    )
