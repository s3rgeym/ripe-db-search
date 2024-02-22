## Описание

Предоставляет API для поиска подсетей в базе RIPE DB.

Схожий функционал предоставляют сервисы типа 2ip, но:

* Там существуют ограничения на количество запросов
* Многие сервисы работают под Cloudflare, который часто блокирует запросы

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
❯ http :9080/addrinfo/ya.ru
HTTP/1.1 200 OK
content-length: 294
content-type: application/json
date: Thu, 22 Feb 2024 05:46:41 GMT
server: uvicorn
x-execution-time: 0.6265822789864615

{
    "inetnum": {
        "cidrs": [
            "77.88.55.0/24"
        ],
        "country": "RU",
        "created": "2012-10-12T12:22:03",
        "descr": "Yandex enterprise network",
        "first_ip": "77.88.55.0",
        "last_ip": "77.88.55.255",
        "last_modified": "2022-04-05T15:29:50",
        "netname": "YANDEX-77-88-55",
        "org": "ORG-YA1-RIPE"
    },
    "input": "ya.ru",
    "ip": "77.88.55.242"
}
```

Поиск подсетей по полям netname, descr, org и country:

```bash
❯ http :9080/search q==sber
HTTP/1.1 200 OK
content-length: 8272
content-type: application/json
date: Thu, 22 Feb 2024 06:14:59 GMT
server: uvicorn
x-execution-time: 0.007384531985735521

{
    "page": 1,
    "pages": 1,
    "per_page": 100,
    "results": [
        {
            "cidrs": [
                "182.75.125.12/30"
            ],
            "country": "IN",
            "created": null,
            "descr": "SBERBANK OF RUSSIA\nn/a\nUGF GOPAL DAS BHAWAN 28 BARAKHAMBA\nROAD New-Delhi-110001 DelhiINdia\nNew-Delhi\nDELHI\nIndia\nContact Person: SANJAY CHAMOLA\n********\nPhone: 1140048887",
            "first_ip": "182.75.125.12",
            "last_ip": "182.75.125.15",
            "last_modified": "2021-01-24T23:18:19",
            "netname": "SBER-2166934-New-Delhi",
            "org": null
        },
        # ...
        {
            "cidrs": [
                "195.56.127.104/29"
            ],
            "country": "HU",
            "created": "2005-09-16T10:05:20",
            "descr": "Schoeler-Bleichmann Phoenix Ltd.\nBudapest",
            "first_ip": "195.56.127.104",
            "last_ip": "195.56.127.111",
            "last_modified": "2021-10-20T13:50:06",
            "netname": "SBER-HU",
            "org": null
        }
    ],
    "total": 33
}
```

> Чтобы искать только по стране добавьте вкруг кода страны пробелы, например, ` ru `

Локальная документация:

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
