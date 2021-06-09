# Запуск сервиса
Советую запускать сервис в dev среде. Там есть относительно подробные логи.
Для этого выполните:
```commandline
docker compose up --build
```
Если хотите production, то:
```commandline
docker compose -f docker-compose.prod.yml up --build
```
Подключитесь к контейнеру `movies_admin`. 
Загрузите fixture с основной базой, чтобы было на чём тестировать:
```commandline
python manage.py loaddata movies.json
```
Для инициализации ElasticSearch выполните команду:
```commandline
python manage.py init_es
``` 
Команда пересоздаёт индекс `movies`, т.е. если индекс создан - то он будет очищен и создан заново.
Кроме того, в базе сбрасывается информация об индексации.

Запустите ETL:
```commandline
python manage.py start_etl
```
