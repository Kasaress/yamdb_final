import random

from django.conf import settings
from django.core.mail import send_mail


def send_confirmation_code(email: str, confirmation_code: str) -> None:
    """Отправляет код подтверждения на почту пользователя."""
    send_mail(
        subject='Код подтверждения',
        message=f'Ваш код: {confirmation_code}',
        from_email=settings.CONTACT_EMAIL,
        recipient_list=[email],
    )


def generate_confirmation_code() -> str:
    """Генерирует код подтверждения."""
    digs = '1234567890'
    code = ''
    for _ in range(settings.CONFIRMATION_CODE_LEN):
        code += random.choice(digs)
    return code
