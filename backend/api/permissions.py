from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrAdmin(BasePermission):
    """
    Разрешает редактировать и удалять рецепт только автору рецепта или
    администратору.
    Доступ на чтение открыт для всех.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff
