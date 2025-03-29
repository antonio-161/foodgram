import hashlib

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from .filters import RecipeFilter
from .pagination import MainPagePagination
from .permissions import IsAuthorOrAdmin
from .serializers import (AvatarSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeListSerializer,
                          RecipeMinifiedSerializer, SetPasswordSerializer,
                          SubscriptionSerializer, TagSerializer,
                          TokenLoginSerializer)
from .utils import generate_shopping_list
from recipes.models import CustomUser, Ingredient, Recipe, Subscription, Tag


class UserViewSet(ModelViewSet):
    """ViewSet для пользователей."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ('email', 'username')
    search_fields = ('username',)

    def get_serializer_class(self):
        """Определяет сериализатор в зависимости от действия."""
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        """Определяет права доступа в зависимости от действия."""
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Переопределяет метод для возврата полного ответа с id
        после создания пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = CustomUserCreateSerializer(
            user, context={'request': request}
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def list(self, request,):
        """Список пользователей."""
        queryset = CustomUser.objects.all()
        paginator = MainPagePagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CustomUserSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=['get'],
            url_path='me',
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = CustomUserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['post'],
            url_path='set_password',
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Изменение пароля пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            {'detail': 'Пароль успешно изменен'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions',
            permission_classes=[IsAuthenticated],
            pagination_class=MainPagePagination)
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        user = request.user
        subscriptions = user.subscriptions.all()

        # Извлечение параметра recipes_limit
        recipes_limit = request.query_params.get('recipes_limit', None)
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                return Response(
                    {'detail': 'Параметр recipes_limit должен быть числом'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscriptions,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            permission_classes=[IsAuthenticated],
            pagination_class=MainPagePagination)
    def subscribe_or_unsubscribe(self, request, pk=None):
        """Подписка или отписка от пользователя."""
        try:
            author = CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'POST':
            if request.user.subscriptions.filter(author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(follower=request.user, author=author)

            # Формирование ответа
            recipes_limit = request.query_params.get('recipes_limit', None)
            if recipes_limit is not None:
                try:
                    recipes_limit = int(recipes_limit)
                except ValueError:
                    return Response(
                        {'detail': 'recipes_limit должен быть числом'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            # Создание подписки через сериализатор
            serializer = SubscriptionSerializer(
                data={'follower': request.user, 'author': author},
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer = SubscriptionSerializer(
                Subscription.objects.get(author=author, follower=request.user),
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                subscription = Subscription.objects.get(
                    author=author, follower=request.user
                )
                subscription.delete()
                return Response(
                    {'detail': 'Подписка успешно удалена.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Subscription.DoesNotExist:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {'detail': 'Метод не поддерживается'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False,
            methods=['put', 'delete'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def add_or_delete_avatar(self, request):
        """Добавление или удаление аватара пользователя."""
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            user = request.user
            user.avatar = serializer.validated_data['avatar']
            user.save()
            return Response(
                {'avatar': user.avatar.url},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            user = request.user
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(
                {'detail': 'Аватар успешно удален'},
                status=status.HTTP_204_NO_CONTENT
            )


class AuthTokenViewSet(ViewSet):
    """ViewSet для аутентификации пользователей."""
    queryset = CustomUser.objects.all()
    serializer_class = TokenLoginSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Получение токена аутентификации."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                'auth_token': token.key,
                'email': user.email,
                'username': user.username
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def logout(self, request):
        """Удаление токена аутентификации."""
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            return Response(
                {'detail': 'Токен не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet для управления тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class RecipeViewSet(ModelViewSet):
    """ViewSet для управления рецептами."""
    queryset = Recipe.objects.all().order_by('-created_at')
    serializer_class = RecipeListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = None

    def get_serializer_class(self):
        """Определяет сериализатор в зависимости от действия."""
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def get_permissions(self):
        """Определяет права доступа в зависимости от действия."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['create']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAuthorOrAdmin()]
        return super().get_permissions()

    def list(self, request):
        """Список рецептов."""
        queryset = self.filter_queryset(self.get_queryset())
        paginator = MainPagePagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RecipeListSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    def handle_action(self, request, pk, action_type):
        """Общий метод для обработки добавления и удаления рецептов."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user_action = getattr(request.user, action_type)

        if request.method == 'POST':
            if user_action.filter(pk=pk).exists():
                return Response(
                    {'detail': f'Рецепт уже находится в {action_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user_action.add(recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not user_action.filter(pk=pk).exists():
                return Response(
                    {'detail': f'Рецепт отсутствует в {action_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user_action.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Метод не поддерживается'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def handle_favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        return self.handle_action(request, pk, 'favorites')

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def handle_shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из списка покупок."""
        return self.handle_action(request, pk, 'shopping_cart')

    @action(detail=False,
            methods=['get'],
            url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Получение списка покупок."""
        shopping_list = generate_shopping_list(request.user)
        return Response(
            shopping_list,
            content_type='text/plain; charset=utf-8',
            status=status.HTTP_200_OK
        )

    @action(detail=True,
            methods=['get'],
            url_path='get-link',
            permission_classes=[AllowAny])
    def short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        base_url = request.build_absolute_uri('/').strip('/')
        unique_hash = hashlib.md5(
            f'recipe-{recipe.id}'.encode()
        ).hexdigest()[:3]
        short_link = f'{base_url}/s/{unique_hash}'
        response_data = {'short-link': short_link}
        return Response(response_data, status=status.HTTP_200_OK)


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet для управления ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['^name']

    def get_queryset(self):
        """Получение списка ингредиентов."""
        name = self.request.query_params.get('name')
        if name:
            return Ingredient.objects.filter(name__istartswith=name)
        return Ingredient.objects.all()
