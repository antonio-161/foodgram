# Foodgram - Продуктовый помощник

**Foodgram** — это веб-приложение, которое позволяет пользователям публиковать рецепты, добавлять их в избранное, составлять список покупок и делиться своими кулинарными идеями с другими. Проект создан для упрощения планирования покупок и приготовления блюд.

## Основные возможности:
- **Регистрация и авторизация пользователей**.
- **Публикация рецептов** с указанием ингредиентов, описанием и изображением.
- **Добавление рецептов в избранное** для быстрого доступа.
- **Формирование списка покупок** на основе выбранных рецептов.
- **Фильтрация рецептов** по тегам (например, завтрак, обед, ужин).
- **Подписка на авторов** для отслеживания их новых рецептов.

## Технологии:
- **Backend**: Python, Django, Django REST Framework.
- **Frontend**: React.
- **База данных**: PostgreSQL.
- **Контейнеризация**: Docker, Docker Compose.
- **Веб-сервер**: Nginx.

## Установка и запуск:
### 1. Клонирование репозитория:
```bash
git clone https://github.com/antonio-161/foodgram.git
cd foodgram
```
### 2. Настройка переменных окружения:
Создайте файл .env в корневой директории и укажите следующие переменные:
```bash
SECRET_KEY=ваш-секретный-ключ
DEBUG=False
ALLOWED_HOSTS=ваш-домен или IP
DB_ENGINE=django.db.backends.postgresql
DB_NAME=имя_базы_данных
POSTGRES_USER=пользователь_базы_данных
POSTGRES_PASSWORD=пароль_базы_данных
DB_HOST=db
DB_PORT=5432
```
### 3. Запуск приложения:
Соберите и запустите контейнеры с помощью Docker Compose:
```bash
docker compose up --build
```
Приложение будет доступно по адресу: http://localhost/.

### 4. Выполнение миграций и сбор статических файлов:
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
```
### 5. Создание суперпользователя:
```bash
docker-compose exec backend python manage.py createsuperuser
```
## Примеры запросов к API
### 1. Создание рецепта (POST /api/recipes/)
Пример запроса:
```bash
{
    "name": "Омлет",
    "ingredients": [
        {
            "id": 1,
            "amount": 2
        }
    ],
    "tags": [1],
    "image": "data:image/png;base64,...",
    "text": "Взбейте яйца и обжарьте на сковороде.",
    "cooking_time": 10
}
```
Пример ответа:
```bash
{
    "id": 1,
    "name": "Омлет",
    "author": {
        "id": 1,
        "username": "chef123"
    },
    "ingredients": [
        {
            "id": 1,
            "name": "Яйцо",
            "measurement_unit": "шт",
            "amount": 2
        }
    ],
    "tags": [
        {
            "id": 1,
            "name": "Завтрак",
            "color": "#E26C2D",
            "slug": "breakfast"
        }
    ],
    "image": "http://localhost/media/recipes/omelette.jpg",
    "text": "Взбейте яйца и обжарьте на сковороде.",
    "cooking_time": 10,
    "is_favorited": false,
    "is_in_shopping_cart": false
}
```
### 2. Получение списка рецептов (GET /api/recipes/)
Пример ответа:
```bash
[
    {
        "id": 1,
        "name": "Омлет",
        "author": {
            "id": 1,
            "username": "chef123"
        },
        "ingredients": [
            {
                "id": 1,
                "name": "Яйцо",
                "measurement_unit": "шт",
                "amount": 2
            }
        ],
        "tags": [
            {
                "id": 1,
                "name": "Завтрак",
                "color": "#E26C2D",
                "slug": "breakfast"
            }
        ],
        "image": "http://localhost/media/recipes/omelette.jpg",
        "text": "Взбейте яйца и обжарьте на сковороде.",
        "cooking_time": 10,
        "is_favorited": false,
        "is_in_shopping_cart": false
    }
]
```

## API документация:
Документация доступна по адресу: http://localhost/api/docs/.

## Автор:
[Антон Степанов]
[https://github.com/antonio-161/]
