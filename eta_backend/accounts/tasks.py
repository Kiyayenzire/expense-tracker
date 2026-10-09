from urllib.parse import quote

from allauth.account.models import EmailAddress, get_emailconfirmation_model
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


def send_registration_verification_email_now(email_address_id):
    email_address = (
        EmailAddress.objects.select_related('user')
        .filter(pk=email_address_id, verified=False)
        .first()
    )
    if email_address is None:
        return False

    confirmation = get_emailconfirmation_model().create(email_address)
    verification_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/#/verify-email/"
        f"{quote(confirmation.key, safe='')}"
    )
    sent_count = send_mail(
        subject='Verify your Expense Tracker account',
        message=(
            f"Hello {email_address.user.username},\n\n"
            'Please verify the email address associated with your account. '
            'This link expires in 24 hours:\n\n'
            f'{verification_url}\n\n'
            'If you did not create this account, you can ignore this message.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email_address.email],
        fail_silently=False,
    )
    if sent_count != 1:
        raise RuntimeError('The verification email was not accepted by the configured email backend.')
    return True


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_registration_verification_email(self, email_address_id):
    try:
        return send_registration_verification_email_now(email_address_id)
    except Exception as error:
        raise self.retry(exc=error)