from recipes.models import Subscription


class IsSubscribedMixin:
    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                author=obj.author if hasattr(obj, 'author') else obj,
                follower=request.user
            ).exists()
        return False
