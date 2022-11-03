
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from reviews import validators

ROLE_CHOICES = (
    (settings.USER, 'Пользователь'),
    (settings.MODERATOR, 'Модератор'),
    (settings.ADMIN, 'Администратор'),
)


class CustomUser(AbstractUser):  # type: ignore
    """Кастомная модель User.
       Позволяет при создании запрашивать емейл и юзернейм.
    """
    username: str = models.CharField(
        'Username',
        unique=True,
        blank=False,
        max_length=settings.USER_NAMES_LENGTH,
        validators=[validators.validate_name, ]
    )
    email: str = models.EmailField(
        'E-mail address',
        unique=True,
        blank=False,
        max_length=settings.EMAIL_LENGTH,
    )
    first_name: str = models.CharField(
        'first name',
        max_length=settings.USER_NAMES_LENGTH,
        blank=True
    )
    last_name: str = models.CharField(
        'last name',
        max_length=settings.USER_NAMES_LENGTH,
        blank=True
    )
    bio: str = models.TextField(
        'Биография пользователя',
        blank=True
    )
    role: str = models.CharField(
        max_length=max(len(role) for role, _ in ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=settings.USER
    )
    confirmation_code: str = models.CharField(
        max_length=settings.CONFIRMATION_CODE_LEN, null=True,
        verbose_name='Код подтверждения',
        default=' '
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_name'
            ),
        ]

    def __str__(self) -> str:
        """Строковое представление модели (отображается в консоли)."""
        return self.username

    @property
    def is_admin(self):
        return (self.role == settings.ADMIN
                or self.is_superuser or self.is_staff)

    @property
    def is_moderator(self):
        return self.role == settings.MODERATOR
