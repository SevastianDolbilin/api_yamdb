from django.contrib import admin

from .models import Category, Comment, Genre, Review, Title


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Админ модель обзоров."""

    list_display = ('id', 'title', 'author_id', 'score', 'pub_date')
    search_fields = ('title__name', 'author_id')
    list_filter = ('score', 'pub_date')
    ordering = ['-pub_date']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Админ модель комментариев."""

    list_display = ('id', 'review', 'author', 'text', 'pub_date')
    search_fields = ('review__title', 'author__username')
    list_filter = ('pub_date',)


class BaseAdmin(admin.ModelAdmin):
    """Базовая админ модель."""

    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    """Админ модель произведения"""

    list_display = ('name', 'year', 'category')
    search_fields = ('name',)
    list_filter = ('category', 'year')
    ordering = ('-year',)
    verbose_name = 'Произведение'
    verbose_name_plural = 'Произведения'


@admin.register(Genre)
class GenreAdmin(BaseAdmin):
    """Админ модель жанра."""

    verbose_name = 'Жанр'
    verbose_name_plural = 'Жанры'


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    """Админ модель категории."""

    verbose_name = 'Категория'
    verbose_name_plural = 'Категории'
