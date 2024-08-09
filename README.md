# Проект - Foodgram

## Подготовка и запуск проекта

1. Клонируйте репозиторий
```
git clone https://github.com/Vasiliy-Blokhin/foodgram/
```
2. Установка на удаленном сервере:
 + Выполните вход на удаленный сервер

 + Установите docker на сервер:
   ```
   sudo apt install docker.io 
   ```
 + Установите docker-compose на сервер:
   ПО инструкции с официального сайта

 + Отредактируйте файл nginx.conf

 + Cоздайте .env файл:

   ```
   SECRET_KEY=<xxx> # ключ вашего проекта (settings)
   DB_ENGINE=<xxx> # указываем с какой базой данных работает проект
   POSTGRES_DB=<xxx> # имя БД, которая будет создана для приложения
   POSTGRES_USER=<xxx> # логин для подключения к БД
   POSTGRES_PASSWORD=<xxx> # пароль для подключения к БД
   DB_HOST=<xxx> # название сервиса (контейнера) 
   DB_PORT=<xxx> # порт для подключения к БД 
   ```
 + Добавьте Secrets:

   Для работы с Workflow добавьте в Secrets GitHub переменные окружения для работы:
   ```
   DB_ENGINE=django.db.backends.postgresql
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432

   DOCKER_PASSWORD=<пароль DockerHub>
   DOCKER_USERNAME=<имя пользователя DockerHub>

   USER=<username для подключения к серверу>
   HOST=<IP сервера>
   PASSPHRASE=<пароль для сервера, если он установлен>
   SSH_KEY=<ваш SSH ключ (для получения команда: cat ~/.ssh/id_rsa)>
   ```
 + После успешного деплоя:
   Перейдите в папку:
   ```
   cd foodgram/infra
   ```
   Обновите образы:
   ```
   sudo docker compose -f docker-compose.production.yml pull
   ```
   Поднимем контейнеры:
   ```
   sudo docker compose -f docker-compose.production.yml up -d
   ```
   Создаем и применяем миграции:
   ```
   sudo docker compose -f docker-compose.production.yml exec backend python3 manage.py makemigrations --noinput
   sudo docker compose -f docker-compose.production.yml exec backend python3 manage.py migrate --noinput
   ```
   Заполните базу данных:
   ```
   sudo docker-compose exec backend python manage.py load_data
   ```
   Супер пользователь уже будет создан:
   ```
   "username": "admin"
   "email": "json@born.com"
   "password": "jbpass123"
   ```


## Работу выполнил:
Василий Блохин.

