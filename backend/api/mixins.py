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
            return obj.author.subscriptions.filter(
                follower=request.user
            ).exists() if hasattr(obj, 'author') else obj.subscriptions.filter(
                follower=request.user
            ).exists()
        return False
