from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from api_yamdb.constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_NAME,
                                 MAX_LENGTH_ROLE, REGEX_USERNAME)


class Role(models.TextChoices):
    """Поле перечисления ролей пользователей."""

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        db_index=True,
        validators=[RegexValidator(
            regex=REGEX_USERNAME,
            message='Недопустимый символ в имени пользователя.'
        )]
    )
    email = models.EmailField(
        'Email',
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
            'invalid': 'Введите корректный email адрес.',
            'blank': 'Это поле не может быть пустым.'
        }
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_NAME,
        blank=True
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_NAME,
        blank=True
    )
    bio = models.TextField(
        'Биография',
        blank=True
    )
    role = models.CharField(
        'Роль',
        max_length=MAX_LENGTH_ROLE,
        choices=Role.choices,
        default=Role.USER.value,
        help_text='Admin, moderator или user. По-умолчанию user.'
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username', )
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='user_email'
            ),
        ]

    def __str__(self) -> str:
        return self.username

    @property
    def is_admin(self):
        return self.role == Role.ADMIN.value

    @property
    def is_moderator(self):
        return self.role == Role.MODERATOR.value

    @property
    def is_user(self):
        return self.role == Role.USER.value
