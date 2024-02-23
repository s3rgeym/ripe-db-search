## Описание

Предоставляет API для поиска сетей в базе RIPE DB.

Да, существуют сервисы типа 2ip, но:

* Там есть ограничения на количество запросов
* Многие работают под Cloudflare, который часто блокирует запросы
* Они ведут логи

## Запуск и требования

Необходимо где-то 4.5 гигабайта свободного места.

Cистемные зависимости:

```bash
yay -S docker{,-compose}
```

Запуск стека:

```bash
$ docker compose up -d
```

В `.env` можно изменить креды от базы, а в `docker-compose.yml` — порты и тд.

В первый раз нужно выкачать и импортировать базу:

```bash
❯ docker compose run app python import_ripe_db.py
[+] Creating 1/0
 ✔ Container postgres  Running                                                                             0.0s
downloaded: https://ftp.ripe.net/ripe/dbase/split/ripe.db.inetnum.gz
downloaded: https://ftp.ripe.net/ripe/dbase/split/ripe.db.inet6num.gz
downloaded: https://ftp.afrinic.net/pub/dbase/afrinic.db.gz
downloaded: https://ftp.apnic.net/pub/apnic/whois/apnic.db.inetnum.gz
downloaded: https://ftp.apnic.net/pub/apnic/whois/apnic.db.inet6num.gz
downloaded: https://ftp.arin.net/pub/rr/arin.db.gz
downloaded: https://ftp.lacnic.net/lacnic/dbase/lacnic.db.gz
import /code/ripe/ripe.db.inetnum.gz
import /code/ripe/ripe.db.inet6num.gz
import /code/ripe/afrinic.db.gz
import /code/ripe/apnic.db.inetnum.gz
import /code/ripe/apnic.db.inet6num.gz
import /code/ripe/arin.db.gz
import /code/ripe/lacnic.db.gz
⠟ total records copied: 6974065
finished at 503.597s
```

Эту операцию нужно повторять по мере необходимости.

Пример: узнаем место, занимаемое базой:

```bash
❯ docker compose exec postgres psql -U ripe_db
psql (16.2)
Type "help" for help.

ripe_db=# \l+
                                                                                       List of databases
   Name    |  Owner  | Encoding | Locale Provider |  Collate   |   Ctype    | ICU Locale | ICU Rules |  Access privileges  |  Size   | Tablespace |                Description
-----------+---------+----------+-----------------+------------+------------+------------+-----------+---------------------+---------+------------+--------------------------------------------
 postgres  | ripe_db | UTF8     | libc            | en_US.utf8 | en_US.utf8 |            |           |                     | 7508 kB | pg_default | default administrative connection database
 ripe_db   | ripe_db | UTF8     | libc            | en_US.utf8 | en_US.utf8 |            |           |                     | 3268 MB | pg_default |
 template0 | ripe_db | UTF8     | libc            | en_US.utf8 | en_US.utf8 |            |           | =c/ripe_db         +| 7353 kB | pg_default | unmodifiable empty database
           |         |          |                 |            |            |            |           | ripe_db=CTc/ripe_db |         |            |
 template1 | ripe_db | UTF8     | libc            | en_US.utf8 | en_US.utf8 |            |           | =c/ripe_db         +| 7572 kB | pg_default | default template for new databases
           |         |          |                 |            |            |            |           | ripe_db=CTc/ripe_db |         |            |
(4 rows)

ripe_db=#
```

## Запросы к API

В примерах используется [httpie](https://httpie.io/).

Получение инормации об адресе:

```bash
❯ http :9080/ipinfo/ya.ru
HTTP/1.1 200 OK
content-length: 380
content-type: application/json
date: Fri, 23 Feb 2024 19:45:59 GMT
server: uvicorn
x-execution-time: 0.01884462800808251

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
        "mnt_by": "YANDEX-MNT",
        "netname": "YANDEX-5-255-255",
        "num_addresses": 256,
        "org": "ORG-YA1-RIPE",
        "source": "RIPE",
        "status": "ASSIGNED PA"
    },
    "input": "ya.ru",
    "ip": "5.255.255.242"
}
```

Поиск подсетей по полям `netname`, `descr`, `org`, `country` и `mnt_by`:

```bash
❯ http :9080/search q=="sberbank" per_page==1
HTTP/1.1 200 OK
content-length: 461
content-type: application/json
date: Fri, 23 Feb 2024 19:46:53 GMT
server: uvicorn
x-execution-time: 0.002507539000362158

{
    "page": 1,
    "pages": 218,
    "per_page": 1,
    "results": [
        {
            "cidrs": [
                "194.186.207.0/24"
            ],
            "country": "RU",
            "created": "1970-01-01T00:00:00",
            "descr": "Savings Bank of the Russian Federation (Sberbank) Vavilova str, 19 Moscow Russia",
            "first_ip": "194.186.207.0",
            "last_ip": "194.186.207.255",
            "last_modified": "2021-11-16T11:05:32",
            "mnt_by": "AS3216-MNT",
            "netname": "RU-SOVINTEL-SBRF-RU",
            "notify": "noc@sovintel.ru",
            "num_addresses": 256,
            "source": "RIPE",
            "status": "ASSIGNED PA"
        }
    ],
    "total": 217
}
```

Параметр `q` поддерживает [специальные операторы](https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY).

> Чтобы искать только по стране добавьте вокруг кода страны пробелы, например, ` ru `

Локальная документация + песочница для выполнения запросов:

* http://localhost:9080/docs

![image](https://github.com/s3rgeym/ripe-db-search/assets/12753171/7e9c00da-8a28-42b9-8f2a-209ff5ce7c83)

Используйте `jq` для обработки результатов.

## PGAdmin

Управление базой через веб-интерфейс:

* Перейдите по адресу http://localhost:5050/
* Для логина используйте email `pgadmin4@pgadmin.org` и пароль `pgadmin4`, сохраните их в браузере
* Добавьте сервер, указав в качестве хоста `postgres`, пользователя и базы `ripe_db` и пароля `ripe_pass`

![image](https://github.com/s3rgeym/ripe-db-search/assets/12753171/3b99a667-33da-4a61-a48e-e4d3fb422222)

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
