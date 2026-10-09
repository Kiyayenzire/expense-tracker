"""
Custom password reset and account management views for the accounts app.
"""
import secrets

from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth import login as django_login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from allauth.account.models import get_emailconfirmation_model

from .serializers import EmailVerificationRegisterSerializer, UserProfileSerializer
from .tasks import send_registration_verification_email

User = get_user_model()


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_options(request):
    configured_providers = set(
        SocialApp.objects.filter(sites__id=settings.SITE_ID, provider__in=['google', 'apple'])
        .values_list('provider', flat=True)
        .distinct()
    )
    return Response({
        'providers': {
            provider: {
                'configured': provider in configured_providers,
                'url': request.build_absolute_uri(f'/accounts/{provider}/login/'),
            }
            for provider in ('google', 'apple')
        },
        'support': {
            'email': settings.SUPPORT_EMAIL,
            'phone': settings.SUPPORT_PHONE,
        },
    })


def social_login_complete(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(f'{settings.FRONTEND_URL}/#/')

    code = secrets.token_urlsafe(32)
    cache.set(f'auth:social-login:{code}', request.user.pk, timeout=60)
    query = urlencode({'code': code})
    return HttpResponseRedirect(f'{settings.FRONTEND_URL.rstrip("/")}/#/social-login?{query}')


@api_view(['POST'])
@permission_classes([AllowAny])
def social_login_exchange(request):
    code = str(request.data.get('code') or '').strip()
    if not code:
        return Response({'detail': 'A social login code is required.'}, status=status.HTTP_400_BAD_REQUEST)

    cache_key = f'auth:social-login:{code}'
    user_id = cache.get(cache_key)
    if user_id is None:
        return Response({'detail': 'This social login link is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
    cache.delete(cache_key)

    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user is None:
        return Response({'detail': 'This account is not active.'}, status=status.HTTP_403_FORBIDDEN)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'key': token.key,
        'user': UserProfileSerializer(user, context={'request': request}).data,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    email = request.data.get('email')
    normalized_email = email.strip().lower() if isinstance(email, str) else ''
    if normalized_email and (
        User.objects.filter(email__iexact=normalized_email).exists()
        or EmailAddress.objects.filter(email__iexact=normalized_email).exists()
    ):
        return Response(
            {'email': ['A user is already registered with this email address.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = EmailVerificationRegisterSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    user = serializer.save(request)
    email_address = EmailAddress.objects.get(user=user, email__iexact=user.email)

    try:
        send_registration_verification_email.delay(email_address.pk)
    except Exception:
        return Response({
            'detail': 'Your account is pending verification, but we could not queue the email. Please use resend verification email to try again.',
            'email': user.email,
            'verification_pending': True,
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'detail': 'Registration received. Check your email to verify your account before signing in.',
        'email': user.email,
        'verification_pending': True,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_registration_verification(request):
    email = str(request.data.get('email') or '').strip()
    if request.user.is_authenticated:
        user = request.user
    elif email:
        user = User.objects.filter(email__iexact=email, is_active=False).first()
    else:
        return Response({'email': ['Enter the email address used to register.']}, status=status.HTTP_400_BAD_REQUEST)

    address = None
    if user and user.email:
        address, _ = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={'primary': True, 'verified': False},
        )

    if address and not address.verified:
        try:
            send_registration_verification_email.delay(address.pk)
        except Exception:
            return Response({
                'detail': 'We could not queue the verification email. Please try again shortly.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'detail': 'If this email belongs to an unverified account, a verification email has been sent.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_registration_email(request):
    key = str(request.data.get('key') or '').strip()
    if not key:
        return Response({'detail': 'A verification key is required.'}, status=status.HTTP_400_BAD_REQUEST)

    confirmation = get_emailconfirmation_model().from_key(key)
    if confirmation is None:
        return Response({'detail': 'This verification link is invalid, expired, or already used.'}, status=status.HTTP_400_BAD_REQUEST)

    email_address = confirmation.confirm(request)
    if email_address is None:
        return Response({'detail': 'This email address could not be verified.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'Email verified. Your account is ready to sign in.'}, status=status.HTTP_200_OK)


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
        return Response({
            'detail': 'Username/email not found. Please check it and try again or create a new account.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(password):
        return Response({
            'detail': 'Incorrect password. Please try again or use the forgot password link.'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not user.is_active:
        email_address = EmailAddress.objects.filter(user=user, email__iexact=user.email).first()
        if email_address and not email_address.verified:
            return Response({
                'detail': 'Please verify your email address before signing in. Check your inbox or resend the verification email.'
            }, status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': 'This account is inactive. Contact support if you need help.'}, status=status.HTTP_403_FORBIDDEN)

    auth_user = authenticate(request, username=user.username, password=password)
    if not auth_user:
        return Response({
            'detail': 'Incorrect password. Please try again or use the forgot password link.'
        }, status=status.HTTP_400_BAD_REQUEST)

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
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Return 200 OK to prevent email enumeration attacks and satisfy API contract tests
        return Response(
            {'detail': 'If an account already exists for this email address, a reset password link has been sent.'},
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
            {'detail': 'If an account already exists for this email address, a reset password link has been sent.'},
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    user = request.user
    if user.has_usable_password():
        return Response(
            {'detail': 'A password is already set. Use Forgot Password to change it.'},
            status=status.HTTP_409_CONFLICT,
        )
    if not EmailAddress.objects.filter(user=user, verified=True).exists():
        return Response(
            {'detail': 'Verify your email address before creating a password.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    new_password = str(request.data.get('new_password') or '')
    confirm_password = str(request.data.get('confirm_password') or '')
    if not new_password or not confirm_password:
        return Response(
            {'detail': 'New password and confirmation are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if new_password != confirm_password:
        return Response(
            {'confirm_password': ['Passwords do not match.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        return Response(
            {'new_password': exc.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save(update_fields=['password'])
    if request.session.get('_auth_user_id') == str(user.pk):
        update_session_auth_hash(request, user)

    return Response({'detail': 'Password set successfully.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_social_account(request):
    provider = str(request.data.get('provider') or '').strip().lower()
    if provider not in {'google', 'apple'}:
        return Response(
            {'provider': ['Choose a linked Google or Apple account.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    password = str(request.data.get('password') or '')
    if not user.has_usable_password() or not password or not user.check_password(password):
        return Response(
            {'password': ['Enter your account password before disconnecting a provider.']},
            status=status.HTTP_403_FORBIDDEN,
        )

    social_account = SocialAccount.objects.filter(user=user, provider=provider).first()
    if social_account is None:
        return Response(
            {'detail': 'That provider is not linked to this account.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    has_other_provider = SocialAccount.objects.filter(user=user).exclude(pk=social_account.pk).exists()
    has_verified_email = EmailAddress.objects.filter(user=user, verified=True).exists()
    if not has_other_provider and not has_verified_email:
        return Response(
            {'detail': 'Verify an email address or connect another sign-in method before disconnecting the last provider.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    social_account.delete()
    providers = sorted(
        set(SocialAccount.objects.filter(user=user).values_list('provider', flat=True))
    )
    return Response({
        'detail': f'{provider.title()} has been disconnected.',
        'social_providers': providers,
    }, status=status.HTTP_200_OK)