from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models import Avg
from django.utils import timezone

from api_yamdb.constants import (LIMIT_LENGTH, MAX_LENGTH, MAX_SCORE_VALUE,
                                 MIN_SCORE_VALUE, REGEX_SLUG_BASE_MODEL,
                                 MIN_VALUE_VALIDATOR)

User = get_user_model()


def max_current_year(value):
    """Динамическая валидация, в зависимости от текущего года."""
    current_year = timezone.now().year
    if value > current_year:
        raise ValidationError(f'Год не может быть больше {current_year}.')


class BaseModel(models.Model):
    """Базовая модель."""

    name = models.CharField(max_length=MAX_LENGTH, verbose_name='Название')
    slug = models.SlugField(
        max_length=LIMIT_LENGTH,
        unique=True,
        verbose_name='Slug',
        validators=[RegexValidator(
            regex=REGEX_SLUG_BASE_MODEL,
            message='Slug может содержать только буквы,'
                    + 'цифры, дефисы и символы подчеркивания.'
        )]
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Genre(BaseModel):
    """Модель жанра."""

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Category(BaseModel):
    """Модель категории."""

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Title(models.Model):
    """Модель произведения."""

    name = models.CharField(max_length=MAX_LENGTH, verbose_name='Название')
    year = models.PositiveIntegerField(
        verbose_name='Год выпуска',
        validators=[
            MinValueValidator(MIN_VALUE_VALIDATOR),
            max_current_year
        ],
    )
    description = models.TextField(
        null=False, blank=True, verbose_name='Описание'
    )
    genre = models.ManyToManyField(
        Genre, verbose_name='Жанры', related_name='titles'
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles'
    )

    @property
    def rating(self):
        return self.reviews.aggregate(Avg('score'))['score__avg']

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'


class Review(models.Model):
    """Модель отзыва."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    text = models.TextField('Текст отзыва', max_length=MAX_LENGTH)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор'
    )
    score = models.PositiveIntegerField(
        'Оценка',
        validators=[
            MinValueValidator(MIN_SCORE_VALUE),
            MaxValueValidator(MAX_SCORE_VALUE)
        ],
        help_text=f"Оценка от {MIN_SCORE_VALUE} до {MAX_SCORE_VALUE}."
    )
    pub_date = models.DateTimeField('Дата публикации', default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'],
                name='unique_author_title'
            )
        ]
        ordering = ['-pub_date']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.author_id} — {self.title} ({self.score})'


class Comment(models.Model):
    """Модель комментария."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )
    text = models.TextField('Текст комментария', max_length=MAX_LENGTH)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField('Дата публикации', default=timezone.now)

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author} комментирует {self.review}'
