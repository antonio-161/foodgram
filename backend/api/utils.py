import csv
from collections import defaultdict
from http import HTTPStatus

from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import CustomUser, Ingredient, IngredientInRecipe


def generate_shopping_list(user):
    """Генерация списка покупок для текущего пользователя."""

    if not user.is_authenticated:
        return HttpResponse(
            'Вы не авторизованы!', status=HTTPStatus.UNAUTHORIZED
        )

    # Собираем список рецептов, добавленных в список покупок пользователя
    shopping_cart = user.shopping_cart.all()

    # Хранилище для ингредиентов и их сумм
    ingredients = defaultdict(
        lambda: {'name': '', 'measurement_unit': '', 'amount': 0}
    )

    # Проходим по каждому рецепту в списке покупок
    ingredients = (
        IngredientInRecipe.objects.filter(recipe__in=shopping_cart)
        .values(
            'ingredient_id',  # ID ингредиента
            'ingredient__name',  # Имя ингредиента
            'ingredient__measurement_unit'  # Единица измерения
        )
        .annotate(total_amount=Sum('amount'))  # Суммируем количество
        .order_by('ingredient__name')  # Сортируем по имени ингредиента
    )

    # Формируем текст для списка покупок
    shopping_list_text = 'Ваш список покупок:\n\n'
    for ingredient in ingredients:
        shopping_list_text += (
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]}) — '
            f'{ingredient["total_amount"]}\n'
        )

    return shopping_list_text


def load_ingredients_from_csv(file_path):
    """
    Загружает ингредиенты из CSV-файла в базу данных.
    """
    with open(file_path, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            name, measurement_unit = row
            Ingredient.objects.get_or_create(
                name=name.strip(),
                measurement_unit=measurement_unit.strip()
            )


def load_users_from_csv(file_path):
    """
    Загружает пользователей из CSV-файла в базу данных.
    Формат CSV: first_name, last_name, username, email, password
    """
    with open(file_path, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            first_name, last_name, username, email, password = row
            if not CustomUser.objects.filter(username=username).exists():
                CustomUser.objects.create_user(
                    username=username.strip(),
                    email=email.strip(),
                    password=password.strip(),
                    first_name=first_name.strip(),
                    last_name=last_name.strip()
                )
