from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтры для рецептов: избранное, список покупок, автор и теги."""
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited', label='Избранное'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart', label='В списке покупок'
    )
    author = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='Автор',
    )
    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='iexact',
        label='Теги',
        method='filter_by_tags'
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по избранным рецептам."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(is_favorited_by__id=user.id)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по рецептам в корзине покупок."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(is_in_shopping_cart__id=user.id)
        return queryset

    def filter_by_tags(self, queryset, name, value):
        """Фильтрация по тегам (по slug)."""
        tag_slugs = self.request.query_params.getlist('tags')
        if tag_slugs:
            return queryset.filter(tags__slug__in=tag_slugs).distinct()
        return queryset
