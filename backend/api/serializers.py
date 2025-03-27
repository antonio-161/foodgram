import base64
import uuid
from io import BytesIO

from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from PIL import Image
from recipes.models import (CustomUser, Favorite, Ingredient,
                            IngredientInRecipe, Recipe, ShoppingCart,
                            Subscription, Tag)
from rest_framework import serializers
from rest_framework.fields import ImageField

from .mixins import IsSubscribedMixin


class CustomUserSerializer(serializers.ModelSerializer, IsSubscribedMixin):
    """Сериализатор для модели CustomUser."""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )


class CustomUserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Создание нового пользователя."""
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для аватара пользователя."""
    avatar = Base64ImageField()


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        """Проверка текущего пароля пользователя."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверный.")
        return value

    def validate_new_password(self, value):
        """Проверка нового пароля пользователя."""
        if value == self.initial_data.get('current_password'):
            raise serializers.ValidationError(
                "Новый пароль не должен совпадать с текущим."
            )
        return value


class TokenLoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя по токену."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        non_fields_errors_key = "detail"

    def validate(self, data):
        """Проверка учетных данных пользователя."""
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {"detail": "Неверный email или пароль."}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Учетная запись отключена."}
            )
        data['user'] = user
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientInRecipe."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'amount', 'name', 'measurement_unit']


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, read_only=True, source='ingredient_in_recipe'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def __init__(self, *args, **kwargs):
        """Инициализация сериализатора."""
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.user = request.user if request else None

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        return self._check_user_related(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        return self._check_user_related(obj, ShoppingCart)

    def _check_user_related(self, obj, model):
        """Проверяет, добавлен ли рецепт в избранное или список покупок."""
        request = self.context.get('request', None)
        if not request or not hasattr(request, 'user'):
            return False
        user = request.user
        return (
            model.objects.filter(user=user, recipe=obj).exists()
            if user.is_authenticated
            else False
        )


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        """
        Переопределение метода to_internal_value для обработки Base64-строки.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            # Декодируем строку Base64
            decoded_file = base64.b64decode(imgstr)

            # Генерируем уникальное имя файла
            filename = f"{uuid.uuid4()}.{ext}"

            # Проверяем тип файла через Pillow
            try:
                image = Image.open(BytesIO(decoded_file))
                file_type = image.format.lower()
                allowed_formats = ['jpeg', 'jpg', 'png', 'gif']
                if file_type not in allowed_formats:
                    raise ValueError(f"Недопустимый тип файла: {file_type}")

                if (
                    file_type != ext
                    and not (file_type == 'jpeg' and ext == 'jpg')
                ):
                    raise ValueError(
                        f"Тип содержимого ({file_type}) не соответствует "
                        f"расширению ({ext})!"
                    )

            except Exception:
                raise ValueError("Не удалось определить тип файла!")

            # Проверяем корректность типа файла
            if file_type != ext:
                raise ValueError("Тип файла не соответствует содержимому!")

            # Возвращаем объект ContentFile
            data = ContentFile(decoded_file, name=filename)

        return super().to_internal_value(data)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    author = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        read_only=True
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField())
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate_cooking_time(self, value):
        """Проверяет, что время приготовления больше или равно 1."""
        if value <= 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть не менее 1 минуты."
            )
        return value

    def validate_ingredients(self, value):
        """
        Проверяет:
        - Список ингредиентов не пустой.
        - Каждый ингредиент имеет нужные поля (id и amount).
        - Количество (amount) больше нуля.
        - Каждый ингредиент существует в базе данных.
        - Отсутствуют повторяющиеся ингредиенты.
        """
        if not value:
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым."
            )

        ingredient_ids = [item['id'] for item in value]
        existing_ingredients = set(
            Ingredient.objects.filter(
                id__in=ingredient_ids).values_list('id', flat=True)
        )
        validated_ingredients = []
        unique_ids = set()

        for item in value:
            if item['id'] not in existing_ingredients:
                raise serializers.ValidationError(
                    f"Ингредиент с ID {item['id']} не существует."
                )
            if item['amount'] <= 0:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть больше 0."
                )
            if item['id'] in unique_ids:
                raise serializers.ValidationError(
                    f"Ингредиент с ID {item['id']} "
                    "встречается более одного раза."
                )

            unique_ids.add(item['id'])
            validated_ingredients.append(item)

        return validated_ingredients

    def validate_tags(self, value):
        """
        Проверяет, что список тегов не пустой и не содержит
        дублирующихся тегов.
        """
        if not value:
            raise serializers.ValidationError(
                "Поле тегов не может быть пустым."
            )

        if len(set(value)) != len(value):
            raise serializers.ValidationError("Список тегов содержит дубли.")

        return value

    def validate_image(self, value):
        """Проверяет, что изображение передано."""
        if not value:
            raise serializers.ValidationError("Изображение обязательно.")
        return value

    def _save_ingredients(self, recipe, ingredients):
        """Сохраняет ингредиенты для рецепта."""
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])
        return recipe

    @transaction.atomic
    def create(self, validated_data):
        """Создает рецепт."""
        validated_data['author'] = self.context['request'].user
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет рецепт."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags:
            instance.tags.set(tags)
        else:
            raise serializers.ValidationError(
                "Поле тегов не может быть пустым."
            )

        if ingredients:
            self._save_ingredients(instance, ingredients)
        else:
            raise serializers.ValidationError(
                "Поле ингредиентов не может быть пустым."
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Переопределяет представление рецепта."""
        return RecipeListSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для минимизированного представления рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer, IsSubscribedMixin):
    """Сериализатор для подписок."""
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    email = serializers.EmailField(source='author.email', read_only=True)
    first_name = serializers.CharField(
        source='author.first_name', read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name', read_only=True
    )
    avatar = serializers.ImageField(source='author.avatar', read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'avatar',
                  'is_subscribed',
                  'recipes',
                  'recipes_count'
                  )

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""
        recipes_limit = self.context.get('recipes_limit', None)
        queryset = Recipe.objects.filter(author=obj.author)
        if recipes_limit:
            queryset = queryset[:recipes_limit]
        return RecipeMinifiedSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return Recipe.objects.filter(author=obj.author).count()
