from django.contrib import admin

from .models import (
    CustomUser,
    Ingredient,
    IngredientInRecipe,
    Favorite,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
    )
    search_fields = ('username', 'email')


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)

    def favorite_count(self, obj):
        return obj.favorited_by.count()
    favorite_count.short_description = 'Добавлений в избранное'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientInRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(Subscription)
