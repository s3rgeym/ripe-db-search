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
❯ docker compose run app python import_ripe_db.py
downloading...
downloaded: https://ftp.ripe.net/ripe/dbase/split/ripe.db.inetnum.gz
downloaded: https://ftp.ripe.net/ripe/dbase/split/ripe.db.inet6num.gz
...
```

Эту операцию нужно по мере необходимости повторять.

## Запросы к API

В примерах используется [httpie](https://httpie.io/).

Получение инормации об адресе:

```bash
❯ http :9080/ipinfo/ya.ru
HTTP/1.1 200 OK
content-length: 418
content-type: application/json
date: Fri, 23 Feb 2024 00:36:50 GMT
server: uvicorn
x-execution-time: 0.025262929004384205

{
    "inetnum": {
        "admin_c": "DUMY-RIPE",
        "cidrs": [
            "77.88.55.0/24"
        ],
        "country": "RU",
        "created": "2012-10-12T12:22:03",
        "descr": "Yandex enterprise network",
        "first_ip": "77.88.55.0",
        "last_ip": "77.88.55.255",
        "last_modified": "2022-04-05T15:29:50",
        "mnt_by": "YANDEX-MNT",
        "netname": "YANDEX-77-88-55",
        "num_addresses": 256,
        "org": "ORG-YA1-RIPE",
        "source": "RIPE",
        "status": "ASSIGNED PA",
        "tech_c": "DUMY-RIPE"
    },
    "input": "ya.ru",
    "ip": "77.88.55.242"
}
```

Поиск подсетей по полям netname, descr, org, country и mnt_by:

```bash
❯ http :9080/search q==sber per_page==3 p==5
HTTP/1.1 200 OK
content-length: 1089
content-type: application/json
date: Fri, 23 Feb 2024 00:39:12 GMT
server: uvicorn
x-execution-time: 3.305883872002596

{
    "page": 5,
    "pages": 12,
    "per_page": 3,
    "results": [
        {
            "admin_c": "DUMY-RIPE",
            "cidrs": [
                "188.246.76.84/30"
            ],
            "country": "BA",
            "created": "2017-09-01T11:10:52",
            "descr": "Sber",
            "first_ip": "188.246.76.84",
            "last_ip": "188.246.76.87",
            "last_modified": "2017-09-01T11:10:52",
            "mnt_by": "BLICNET-MNT",
            "netname": "Blicnet",
            "notify": "ripe@blic.net",
            "num_addresses": 4,
            "source": "RIPE",
            "status": "ASSIGNED PA",
            "tech_c": "DUMY-RIPE"
        },
        {
            "admin_c": "DUMY-RIPE",
            "cidrs": [
                "78.37.87.64/29"
            ],
            "country": "RU",
            "created": "2016-09-15T11:34:01",
            "descr": "PAO Sberbank, banking",
            "first_ip": "78.37.87.64",
            "last_ip": "78.37.87.71",
            "last_modified": "2016-09-15T11:34:01",
            "mnt_by": "AS8997-MNT",
            "netname": "RU-SBER-8626",
            "notify": "autom@baltnet.ru",
            "num_addresses": 8,
            "source": "RIPE",
            "status": "ASSIGNED PA",
            "tech_c": "DUMY-RIPE"
        },
        {
            "admin_c": "DUMY-RIPE",
            "cidrs": [
                "78.37.87.56/29"
            ],
            "country": "RU",
            "created": "2016-09-02T13:06:26",
            "first_ip": "78.37.87.56",
            "last_ip": "78.37.87.63",
            "last_modified": "2016-09-02T13:06:26",
            "mnt_by": "AS8997-MNT",
            "netname": "RU-SBER-7382",
            "num_addresses": 8,
            "source": "RIPE",
            "status": "ASSIGNED PA",
            "tech_c": "DUMY-RIPE"
        }
    ],
    "total": 33
}
```

> Чтобы искать только по стране добавьте вокруг кода страны пробелы, например, ` ru `

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
