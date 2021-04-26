Коротко о реализации задания:

# Задание 1
Для запуска контейнера с PostgreSQL, в котором автоматически создаётся схема, просто запустите 
```docker-compose up```. Этот же контейнер пригодится в следующих заданиях.

# Задание 2
Убедитесь, что зависимости установлены

```commandline
cd ./sqlite_to_postgres
pip install requirements.txt -r
```

Запустите скрипт `load_data.py`.

# Задание 3
Убедитесь, что зависимости установлены

```commandline
cd ./movies_admin
pip install -r requirements/dev.txt
```
Примените миграции. Изначальная миграция для приложения `movies` должна быть с флагом `--fake`,
т.к. схема уже существует.
```commandline
manage.py migrate movies 0001 --fake
manage.py migrate 
```
Создайте профиль администратора, запустите сервер.
```commandline
manage.py createsuperuser
manage.py runserver 
```
Для создания тестовых данных можете воспользоваться командой
```commandline
manage.py generate_test_data
```
На данный момент параметры объёма тестовых данных редактируются в исходном коде