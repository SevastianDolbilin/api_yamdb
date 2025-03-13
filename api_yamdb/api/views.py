from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.tokens import default_token_generator
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Review, Title
from .paginations import CategoryPagination, GenrePagination
from .permissions import (IsAnonymous, IsAuthor, IsModerator,
                          IsSuperUserOrIsAdmin)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer,
                          TitleReadSerializer, TitleWriteSerializer,
                          TokenCreateSerializer, UserCreateSerializer,
                          UserSerializer)
from .utils import send_confirmation_code

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Представление для взаимодействия с пользователем, создание
    пользователя администратором, удаление/изменение/получение пользователя.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('username', )
    permission_classes = (IsSuperUserOrIsAdmin, )

    @action(
        detail=False,
        methods=['get', 'patch', 'delete'],
        url_path=r'(?P<username>[\w.@+-]+)'
    )
    def user_by_username(self, request, username):
        """Изменение данных учетной записи конкретного пользователя."""
        user = get_object_or_404(User, username=username)
        if request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def user_by_me(self, request):
        """Изменение данных своей учетной записи."""
        if request.method == 'PATCH':
            data = request.data.copy()
            data.pop('role', None)
            serializer = UserSerializer(
                request.user, data=data, partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserCreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Представление для работы с пользователем, создание пользователя
    самостоятельно.
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = (permissions.AllowAny, )

    def create(self, request):
        """Создание пользователя и генерация кода поддтверждения
        через email.
        """
        serializer = UserCreateSerializer(data=request.data)
        user_username = User.objects.filter(
            username=request.data.get('username')
        ).first()
        user_email = User.objects.filter(
            email=request.data.get('email')
        ).first()
        if (
            user_username
            and user_username.email == serializer.initial_data.get('email')
        ):
            confirmation_code = default_token_generator.make_token(
                user_username
            )
            send_confirmation_code(user_username.email, confirmation_code)
            return Response(
                {
                    'email': user_username.email,
                    'username': user_username.username
                },
                status=status.HTTP_200_OK
            )
        elif user_username and user_email:
            return Response(
                {
                    'email': [
                        user_email.email
                    ],
                    'username': [
                        user_username.username
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.is_valid(raise_exception=True)
        user = User.objects.create(**serializer.validated_data)
        confirmation_code = default_token_generator.make_token(user)
        send_confirmation_code(user.email, confirmation_code)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenCreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Представление для работы с токеном."""

    queryset = User.objects.all()
    serializer_class = TokenCreateSerializer
    permission_classes = (permissions.AllowAny, )

    def create(self, request):
        """Генерация токена на основе кода подтверждения."""

        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        user = get_object_or_404(User, username=username)
        confirmation_code = serializer.validated_data.get('confirmation_code')
        if not default_token_generator.check_token(user, confirmation_code):
            message = {'token': 'Ошибка валидации токена.'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        access_token = str(AccessToken.for_user(user))
        message = {'token': access_token}
        return Response(message, status=status.HTTP_200_OK)


class BaseViewSet(
        mixins.DestroyModelMixin,
        mixins.CreateModelMixin,
        mixins.ListModelMixin,
        viewsets.GenericViewSet):
    """Базовое представление с возможностью создания/удаления/получения
    данных. Создание/удаление доступны администратору, безопасные методы
    доступны анонимному пользователю. Есть возможность поиска и фильтрации.
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'slug']
    search_fields = ('name', 'slug',)
    permission_classes = (IsSuperUserOrIsAdmin | IsAnonymous,)
    lookup_field = 'slug'


class CategoryViewSet(BaseViewSet):
    """Представление для модели категорий, наследуемое от
    базового представления."""

    queryset = Category.objects.all().order_by('slug')
    serializer_class = CategorySerializer


class GenreViewSet(BaseViewSet):
    """Представление для модели жаноров, наследуемое от
    базового представления."""

    queryset = Genre.objects.all().order_by('slug')
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Представление для работы с произведениями."""

    queryset = Title.objects.all().order_by('name')
    permission_classes = (IsSuperUserOrIsAdmin | IsAnonymous,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('category__slug', 'genre__slug', 'name', 'year')
    search_fields = ('category__slug', 'genre__slug', 'name', 'year',)

    def get_queryset(self):
        """Возвращает базовый queryset с применением пользовательского
        пагинатора в зависимости от переданных параметров запроса."""

        queryset = super().get_queryset()
        if 'genre' in self.request.query_params:
            self.pagination_class = GenrePagination
        elif 'category' in self.request.query_params:
            self.pagination_class = CategoryPagination
        return queryset

    def update(self, request, *args, **kwargs):
        """Возращает статус ошибки 405 METHOD NOT ALLOWED
        в случае отправки запроса PUT."""

        if request.method == 'PUT':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def get_serializer_class(self):
        """Возращает подходящий сериализатор в зависимости от запроса."""
        if self.request.method in ['POST', 'PATCH']:
            return TitleWriteSerializer
        return TitleReadSerializer

    def create(self, request, *args, **kwargs):
        """После создания, результат выводит через сериализатор
        используемый для получения данных."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = TitleReadSerializer(serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def partial_update(self, request, *args, **kwargs):
        """После обновления, результат выводит через сериализатор
        используемый для получения данных."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = TitleReadSerializer(serializer.instance)
        return Response(
            read_serializer.data,
            status=status.HTTP_200_OK
        )


class BaseTitleReviewViewSet(viewsets.ModelViewSet):
    """Базовое представление для работы с объектами Title и Review.

    Содержит общую логику, которая используется в других вьюсетах,
    связанных с отзывами и произведениями.
    """

    def get_title(self):
        """Получает и возвращает объект Title на основе переданного title_id.
        Использует `title_id` из URL-параметров для получения объекта Title.
        Если объект не найден, возвращает 404 ошибку.

        Returns:
            Title: Объект Title, соответствующий заданному title_id.
        """
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Title, id=title_id)

    def get_review(self):
        """Получает и возвращает объект Review на основе переданного review_id.
        Использует `review_id` из URL-параметров для получения объекта Review.
        Если объект не найден, возвращает 404 ошибку.

        Returns:
            Review: Объект Review, соответствующий заданному review_id.
        """
        review_id = self.kwargs.get('review_id')
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(
            Review, id=review_id, title_id=title_id
        )

    def update(self, request, *args, **kwargs):
        """Ограничение на приенение метода 'PUT'."""
        if request.method == 'PUT':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def get_permissions(self):
        """Определяет разрешения для методов вьюсета на основе типа запроса.

        Returns:
            list: Список классов разрешений для данного запроса.
        """
        if self.request.method in ['POST', 'PUT']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.request.method in ['PATCH', 'DELETE']:
            permission_classes = [
                IsAuthor | IsModerator | IsSuperUserOrIsAdmin
            ]
        else:
            permission_classes = [IsAnonymous]
        return [permission() for permission in permission_classes]


class ReviewViewSet(BaseTitleReviewViewSet):
    """Представление для работы с отзывами.
    Предоставляет методы для создания, получения, обновления и удаления
    отзывов.
    """

    serializer_class = ReviewSerializer

    def get_queryset(self):
        """Получает набор отзывов, связанных с конкретным произведением.

        Returns:
            QuerySet: Набор отзывов, связанных с объектом Title.
        """
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        """Сохраняет новый отзыв, устанавливая автора и произведение.

        Args:
            serializer (Serializer): Сериализатор для создания нового отзыва.
        """
        serializer.save(
            author=self.request.user,
            title=self.get_title()
        )

    def get_serializer_context(self):
        """Получает контекст для сериализатора.
        Добавляет объект Title в контекст для доступа в сериализаторе.

        Returns:
            dict: Контекст для сериализатора.
        """
        context = super().get_serializer_context()
        context['title'] = self.get_title()
        return context


class CommentViewSet(BaseTitleReviewViewSet):
    """Представление для работы с комментариями.
    Предоставляет методы для создания, получения, обновления и удаления
    комментариев.
    """

    serializer_class = CommentSerializer

    def get_queryset(self):
        """Получает набор комментариев, связанных с конкретным отзывом.

        Returns:
            QuerySet: Набор комментариев, связанных с объектом Review.
        """
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        """Сохраняет новый комментарий, устанавливая автора и отзыв.

        Args:
            serializer (Serializer): Сериализатор для создания нового
            комментария.
        """

        serializer.save(
            author=self.request.user,
            review=self.get_review()
        )
