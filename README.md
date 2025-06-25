# Foodgram — Продуктовый помощник

**Foodgram** — это современное веб-приложение для публикации и поиска кулинарных рецептов, формирования списка покупок и планирования питания. Проект позволяет пользователям делиться рецептами, добавлять их в избранное, подписываться на любимых авторов и быстро формировать список необходимых ингредиентов.

## 🚀 Основные возможности

- Регистрация и авторизация пользователей
- Публикация рецептов с ингредиентами, описанием и изображением
- Добавление рецептов в избранное
- Формирование и скачивание списка покупок
- Фильтрация рецептов по тегам (например, завтрак, обед, ужин)
- Подписка на авторов рецептов
- Документация и тестовые запросы к API

## 🛠️ Технологии

- **Backend:** Python, Django, Django REST Framework, Djoser
- **Frontend:** React
- **База данных:** PostgreSQL
- **Контейнеризация:** Docker, Docker Compose
- **Веб-сервер:** Nginx

## ⚡ Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/antonio-161/foodgram.git
cd foodgram
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корневой директории и заполните его по примеру из [.env.example](.env.example):

```env
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

### 3. Сборка и запуск контейнеров

```bash
docker compose up --build
```

Приложение будет доступно по адресу: [http://localhost/](http://localhost/)

### 4. Миграции и сбор статики

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
```

### 5. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```

## 📚 Документация и тестирование API

- Swagger/OpenAPI: [http://localhost/api/docs/](http://localhost/api/docs/)
- Готовая коллекция запросов для Postman: [postman_collection/foodgram.postman_collection.json](postman_collection/foodgram.postman_collection.json)
- Инструкция по тестированию API: [postman_collection/README.md](postman_collection/README.md)

## 📝 Примеры запросов к API

### Создание рецепта

`POST /api/recipes/`

```json
{
  "name": "Омлет",
  "ingredients": [
    { "id": 1, "amount": 2 }
  ],
  "tags": [1],
  "image": "data:image/png;base64,...",
  "text": "Взбейте яйца и обжарьте на сковороде.",
  "cooking_time": 10
}
```

### Получение списка рецептов

`GET /api/recipes/`

```json
[
  {
    "id": 1,
    "name": "Омлет",
    "author": { "id": 1, "username": "chef123" },
    "ingredients": [
      { "id": 1, "name": "Яйцо", "measurement_unit": "шт", "amount": 2 }
    ],
    "tags": [
      { "id": 1, "name": "Завтрак", "color": "#E26C2D", "slug": "breakfast" }
    ],
    "image": "http://localhost/media/recipes/omelette.jpg",
    "text": "Взбейте яйца и обжарьте на сковороде.",
    "cooking_time": 10,
    "is_favorited": false,
    "is_in_shopping_cart": false
  }
]
```

## 🏗️ CI/CD

Автоматизация сборки, тестирования и деплоя реализована через GitHub Actions ([.github/workflows/main.yml](.github/workflows/main.yml)).  
При пуше в ветку `main` происходит:

- Проверка кода линтером flake8
- Сборка и публикация Docker-образов backend и frontend на DockerHub
- Автоматический деплой на сервер

## 👤 Автор

- [Антон Степанов](https://github.com/antonio-161)

---

> Foodgram — ваш помощник в мире кулинарии!