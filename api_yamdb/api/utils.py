from django.core.mail import send_mail

from django.conf import settings


def send_confirmation_code(email, confirmation_code):
    """Отправка кода подтверждения на почту пользователя."""
    send_mail(
        subject='Код подтверждения',
        message=f'Ваш код подтверждения: {confirmation_code}',
        from_email=settings.EMAIL_YAMDB,
        recipient_list=(email, ),
        fail_silently=False,
    )
