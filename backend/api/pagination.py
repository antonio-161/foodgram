from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MainPagePagination(PageNumberPagination):
    """Пагинация для главной страницы."""
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Возвращает ответ с пагинацией."""
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
