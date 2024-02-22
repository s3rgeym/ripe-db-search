## Описание

Предоставляет API для поиска подсетей в базе RIPE DB.

Схожий функционал предоставляют сервисы типа 2ip, но:

* Там существуют ограничения на количество запросов
* Многие сервисы работают под Cloudflare, который часто блокирует запросы
* Они ведут логи

## Установка

Установите системные зависимости:

```bash
yay -S docker{,-compose}
```

## Запуск

Запуск стека:

```bash
$ docker compose up -d
```

В `.env` можно изменить креды от базы.


В первый раз нужно выкачать и импортировать базу:

```bash
$ docker compose run app python import_ripe_db.py
```

Эту операцию нужно периодически повторять.

## Запросы к API

Получение инормации об адресе:

```bash
❯ http :9080/ipinfo/ya.ru
HTTP/1.1 200 OK
content-length: 319
content-type: application/json
date: Thu, 22 Feb 2024 17:02:53 GMT
server: uvicorn
x-execution-time: 0.019827787997201085

{
    "inetnum": {
        "cidrs": [
            "5.255.255.0/24"
        ],
        "country": "RU",
        "created": "2013-04-25T13:29:22",
        "descr": "Yandex enterprise network",
        "first_ip": "5.255.255.0",
        "last_ip": "5.255.255.255",
        "last_modified": "2022-04-05T15:29:03",
        "netname": "YANDEX-5-255-255",
        "num_addresses": 256,
        "org": "ORG-YA1-RIPE"
    },
    "input": "ya.ru",
    "ip": "5.255.255.242"
}
```

Поиск подсетей по полям netname, descr, org и country:

```bash
❯ http :9080/search q==sber per_page==3 p==5
HTTP/1.1 200 OK
content-length: 723
content-type: application/json
date: Thu, 22 Feb 2024 18:15:02 GMT
server: uvicorn
x-execution-time: 0.005476296006236225

{
    "page": 5,
    "pages": 12,
    "per_page": 3,
    "results": [
        {
            "cidrs": [
                "188.246.76.84/30"
            ],
            "country": "BA",
            "created": "2017-09-01T11:10:52",
            "descr": "Sber",
            "first_ip": "188.246.76.84",
            "last_ip": "188.246.76.87",
            "last_modified": "2017-09-01T11:10:52",
            "netname": "Blicnet",
            "num_addresses": 4
        },
        {
            "cidrs": [
                "78.37.87.64/29"
            ],
            "country": "RU",
            "created": "2016-09-15T11:34:01",
            "descr": "PAO Sberbank, banking",
            "first_ip": "78.37.87.64",
            "last_ip": "78.37.87.71",
            "last_modified": "2016-09-15T11:34:01",
            "netname": "RU-SBER-8626",
            "num_addresses": 8
        },
        {
            "cidrs": [
                "78.37.87.56/29"
            ],
            "country": "RU",
            "created": "2016-09-02T13:06:26",
            "first_ip": "78.37.87.56",
            "last_ip": "78.37.87.63",
            "last_modified": "2016-09-02T13:06:26",
            "netname": "RU-SBER-7382",
            "num_addresses": 8
        }
    ],
    "total": 33
}
```

> Чтобы искать только по стране добавьте вкруг кода страны пробелы, например, ` ru `

Локальная документация + песочница для выполнения запросов:

* http://localhost:9080/docs

Используйте `jq` для обработки результатов.

## PGAdmin

* Перейдите по адресу http://localhost:5050/
* Для логина используйте email `pgadmin4@pgadmin.org` и пароль `pgadmin4`, сохраните их в браузере
* Добавьте сервер, указав в качестве хоста `postgres`, пользователя и базы `ripe_db` и пароля `ripe_pass`

## Разработка

Тут в принципе описан весь процесс разработки через Dev Containers с использованием Compose.

`Ctrl-Shift-P`, `Dev Containers: Open Folder in Container`, а далее запускаем дебагер...

Если нужно пересоздать ... > `Add configuration to workspace` > `From 'docker-compose.yml'`, выбираем `app` (питоновское приложение, которое будет отлаживать)

Чтобы не ставить расширения вручную, можно их прописать в `.devcontainer/devcontainer.json`:
```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.vscode-pylance",
        "ms-python.python",
        "ms-python.pylint",
        "ms-python.isort",
        "ms-python.debugpy",
        "ms-python.black-formatter"
      ]
    }
  }
}
```

При изменении ... нужно запускать `Dev Containers: Rebuild Container` или `Dev Containers: Rebuild Container Without Cache` (чтобы еще пересобрать и контейнер сервиса).

Некоторые расширения могут не установиться:

```
Unable to install extension 'XXX' as it is not compatible with VS Code 'X.X.X'.
```

Их придется доставить вручную, выбрав pre release version.

Установка модулей, используя `pyproject.toml`:

```bash
# установка без зависимостей для разработчика
pip install .

# ...
pip install '.[dev]'
```

Зависимости в том же файле прописывать

Настройка pylint: см `pylintrc`, ищи `[MESSAGES CONTROL]`, `disable=`.
