from recipes.models import Subscription


class IsSubscribedMixin:
    def get_is_subscribed(self, obj):
        """
        Проверяет:
        - подписан ли текущий пользователь на данного пользователя;
        - подписку на самого себя.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Проверка на подписку на самого себя
            if (obj.author == request.user if hasattr(obj, 'author')
                    else obj == request.user):
                return False
            # Проверка на подписку на другого автора
            return Subscription.objects.filter(
                author=obj.author if hasattr(obj, 'author') else obj,
                follower=request.user
            ).exists()
        return False
