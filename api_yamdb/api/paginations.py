from rest_framework.pagination import PageNumberPagination

from api_yamdb.constants import (MAX_PAGINATION_VALUE, MIDDLE_PAGINATION_VALUE,
                                 MIN_PAGINATION_VALUE)


class GenrePagination(PageNumberPagination):
    """Кастомный пагинатор для фильтрации по жанрам."""

    page_size = MIDDLE_PAGINATION_VALUE
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGINATION_VALUE


class CategoryPagination(PageNumberPagination):
    """Кастомный пагинатор для фильтрации по категориям."""

    page_size = MIN_PAGINATION_VALUE
    page_size_query_param = 'page_size'
