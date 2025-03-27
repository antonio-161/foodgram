from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import (EMAIL_MAX_LENGTH, MU_MAX_LENGTH, NAME_MAX_LENGTH,
                        PASSWORD_MAX_LENGTH, RECIPE_MAX_LENGTH, TAG_MAX_LENGTH)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта',
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
            'blank': 'Email не может быть пустым.'
        }
    )
    username = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        null=False,
        blank=False,
        verbose_name='Имя пользователя',
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    '''Имя пользователя может содержать только буквы,
                    цифры и @/./+/-/_ символы.'''
                ),
            )
        ],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
            'blank': 'Имя пользователя не может быть пустым.'
        }
    )
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Фамилия',
    )
    password = models.CharField(
        max_length=PASSWORD_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Пароль',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )
    shopping_cart = models.ManyToManyField(
        'Recipe',
        through='ShoppingCart',
        verbose_name='Список покупок',
        related_name='user_shopping_cart',
    )
    favorites = models.ManyToManyField(
        'Recipe',
        through='Favorite',
        verbose_name='Избранное',
        related_name='user_favorites',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Уникальный слаг тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        default_related_name = 'tags'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        max_length=PASSWORD_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MU_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'

    def __str__(self):
        return f"{self.name} - {self.measurement_unit}"


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        null=False,
        blank=False,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=RECIPE_MAX_LENGTH,
        blank=False,
        null=False,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=False,
        null=False,
        verbose_name='Изображение рецепта'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    cooking_time = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name='Время приготовления (в минутах)'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    is_favorited_by = models.ManyToManyField(
        CustomUser,
        through='Favorite',
        verbose_name='Избранные рецепты',
        related_name='favorite_recipes',
    )
    is_in_shopping_cart = models.ManyToManyField(
        CustomUser,
        through='ShoppingCart',
        verbose_name='Список покупок',
        related_name='recipes_in_shopping_cart',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания рецепта'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['id']

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель ингредиента в рецепте."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return (
            f"{self.recipe.name}: "
            f"{self.ingredient.name} - {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites_list',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} добавил в избранное {self.recipe.name}"


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart_list',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} добавил {self.recipe.name}" \
            "в список покупок"


class Subscription(models.Model):
    """Модель подписки."""
    follower = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        default=None,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('follower', 'author')
        ordering = ['id']

    def __str__(self):
        return f"{self.follower.username} подписан на {self.author.username}"
