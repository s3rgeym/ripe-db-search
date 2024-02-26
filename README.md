## Описание

Предоставляет API для поиска сетей в базе RIPE DB. Еще понятнее: я взял распарсил базу RIPE, организации-монополиста (осуждаю) со штаб-квартирой в пидерландах (их тоже осуждаю ибо нехуй), которая распределяет блоки ip-адресов между всякими хостинг-провайдерами и прочим около-IT, и прикрутил к ней поисковик.

Если не нужен какой-то продвинутый поиск, используйте [ripe-ip-seach](https://github.com/s3rgeym/ripe-ip-seach):

```bash
$ pipx install ripe-ip-search
Installing to existing venv 'ripe_ip_search'
  installed package ripe_ip_search 0.1.0, installed using Python 3.11.7
  These apps are now globally available
    - ripe-ip-search
done! ✨ 🌟 ✨

$ ripe-ip-search -h
usage: ripe-ip-search [-h] [-v] search_term

Search ip adresses using RIPE DB

positional arguments:
  search_term

options:
  -h, --help       show this help message and exit
  -v, --verbosity  increase verbosity level
```

Да, существуют сервисы официальные и сторонние типа 2ip, но:

* Там есть ограничения на количество запросов
* Многие работают под Cloudflare, который часто блокирует запросы
* Они ведут логи и доступ к ним может быть заблокирован из России

Пример получения информации о своем ip через ripe.net:

```bash
curl 'https://rest.db.ripe.net/search.json?query-string='$(curl -s ifconfig.me)'&flags=no-filtering&type-filter=inetnum'
```
Но если с ним поэксперементировать, то обнаружится, что искать можно только по полному соотвествию, мз-за чего и был сохдан этот проект. 

<details>
 <summary>Парсинг ответа на Python</summary>
 
```python
>>> r = requests.get('https://rest.db.ripe.net/search.json', {'query-string': '77.88.55.242', 'flags': 'no-filtering', 'type-filter': 'inetnum'})
>>> data = r.json()
>>> data.keys()
dict_keys(['service', 'parameters', 'objects', 'terms-and-conditions', 'version'])
>>> data['objects']
{'object': [{'type': 'inetnum', 'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/inetnum/77.88.55.0 - 77.88.55.255'}, 'source': {'id': 'ripe'}, 'primary-key': {'attribute': [{'name': 'inetnum', 'value': '77.88.55.0 - 77.88.55.255'}]}, 'attributes': {'attribute': [{'name': 'inetnum', 'value': '77.88.55.0 - 77.88.55.255'}, {'name': 'netname', 'value': 'YANDEX-77-88-55'}, {'name': 'status', 'value': 'ASSIGNED PA'}, {'name': 'country', 'value': 'RU'}, {'name': 'descr', 'value': 'Yandex enterprise network'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/role/YNDX1-RIPE'}, 'name': 'admin-c', 'value': 'YNDX1-RIPE', 'referenced-type': 'role'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/role/YNDX1-RIPE'}, 'name': 'tech-c', 'value': 'YNDX1-RIPE', 'referenced-type': 'role'}, {'name': 'remarks', 'value': 'INFRA-AW'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/organisation/ORG-YA1-RIPE'}, 'name': 'org', 'value': 'ORG-YA1-RIPE', 'referenced-type': 'organisation'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/mntner/YANDEX-MNT'}, 'name': 'mnt-by', 'value': 'YANDEX-MNT', 'referenced-type': 'mntner'}, {'name': 'source', 'value': 'RIPE'}, {'name': 'created', 'value': '2012-10-12T12:22:03Z'}, {'name': 'last-modified', 'value': '2022-04-05T15:29:50Z'}]}}, {'type': 'organisation', 'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/organisation/ORG-YA1-RIPE'}, 'source': {'id': 'ripe'}, 'primary-key': {'attribute': [{'name': 'organisation', 'value': 'ORG-YA1-RIPE'}]}, 'attributes': {'attribute': [{'name': 'organisation', 'value': 'ORG-YA1-RIPE'}, {'name': 'org-name', 'value': 'YANDEX LLC'}, {'name': 'country', 'value': 'RU'}, {'name': 'org-type', 'value': 'LIR'}, {'name': 'address', 'value': 'LVA TOLSTOY STREET, 16'}, {'name': 'address', 'value': '119021'}, {'name': 'address', 'value': 'Moscow'}, {'name': 'address', 'value': 'RUSSIAN FEDERATION'}, {'name': 'phone', 'value': '+74957397000'}, {'name': 'fax-no', 'value': '+74957397070'}, {'name': 'e-mail', 'value': 'noc@yandex.net'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/person/MK24579-RIPE'}, 'name': 'admin-c', 'value': 'MK24579-RIPE', 'referenced-type': 'person'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/person/AUR2-RIPE'}, 'name': 'admin-c', 'value': 'AUR2-RIPE', 'referenced-type': 'person'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/person/EM3673-RIPE'}, 'name': 'admin-c', 'value': 'EM3673-RIPE', 'referenced-type': 'person'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/role/YAH6-RIPE'}, 'name': 'abuse-c', 'value': 'YAH6-RIPE', 'referenced-type': 'role'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/mntner/RIPE-NCC-HM-MNT'}, 'name': 'mnt-ref', 'value': 'RIPE-NCC-HM-MNT', 'referenced-type': 'mntner'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/mntner/YANDEX-MNT'}, 'name': 'mnt-ref', 'value': 'YANDEX-MNT', 'referenced-type': 'mntner'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/mntner/RIPE-NCC-HM-MNT'}, 'name': 'mnt-by', 'value': 'RIPE-NCC-HM-MNT', 'referenced-type': 'mntner'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/mntner/YANDEX-MNT'}, 'name': 'mnt-by', 'value': 'YANDEX-MNT', 'referenced-type': 'mntner'}, {'name': 'created', 'value': '2004-04-22T14:39:02Z'}, {'name': 'last-modified', 'value': '2023-07-17T08:05:45Z'}, {'name': 'source', 'value': 'RIPE'}]}}, {'type': 'role', 'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/role/YNDX1-RIPE'}, 'source': {'id': 'ripe'}, 'primary-key': {'attribute': [{'name': 'nic-hdl', 'value': 'YNDX1-RIPE'}]}, 'attributes': {'attribute': [{'name': 'role', 'value': 'Yandex LLC Network Operations'}, {'name': 'address', 'value': 'Yandex LLC'}, {'name': 'address', 'value': '16, Leo Tolstoy St.'}, {'name': 'address', 'value': '119021'}, {'name': 'address', 'value': 'Moscow'}, {'name': 'address', 'value': 'Russian Federation'}, {'name': 'phone', 'value': '+7 495 739 7000'}, {'name': 'fax-no', 'value': '+7 495 739 7070'}, {'name': 'e-mail', 'value': 'noc@yandex.net'}, {'name': 'remarks', 'value': 'trouble: ------------------------------------------------------'}, {'name': 'remarks', 'value': 'trouble: Points of contact for Yandex LLC Network Operations'}, {'name': 'remarks', 'value': 'trouble: ------------------------------------------------------'}, {'name': 'remarks', 'value': 'trouble: Routing and peering issues: noc@yandex.net'}, {'name': 'remarks', 'value': 'trouble: SPAM issues: abuse@yandex.ru'}, {'name': 'remarks', 'value': 'trouble: Network security issues: abuse@yandex.ru'}, {'name': 'remarks', 'value': 'trouble: Mail issues: postmaster@yandex.ru'}, {'name': 'remarks', 'value': 'trouble: General information: info@yandex.ru'}, {'name': 'remarks', 'value': 'trouble: ------------------------------------------------------'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/person/MK24579-RIPE'}, 'name': 'admin-c', 'value': 'MK24579-RIPE', 'referenced-type': 'person'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/person/EM3673-RIPE'}, 'name': 'tech-c', 'value': 'EM3673-RIPE', 'referenced-type': 'person'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/person/AUR2-RIPE'}, 'name': 'tech-c', 'value': 'AUR2-RIPE', 'referenced-type': 'person'}, {'name': 'nic-hdl', 'value': 'YNDX1-RIPE'}, {'link': {'type': 'locator', 'href': 'https://rest.db.ripe.net/ripe/mntner/YANDEX-MNT'}, 'name': 'mnt-by', 'value': 'YANDEX-MNT', 'referenced-type': 'mntner'}, {'name': 'created', 'value': '2002-06-07T05:35:50Z'}, {'name': 'last-modified', 'value': '2021-08-23T16:42:06Z'}, {'name': 'source', 'value': 'RIPE'}, {'name': 'abuse-mailbox', 'value': 'abuse@yandex.ru'}]}}]}
>>> [{x['name']: x['value'] for x in item['attributes']['attribute']} for item in filter(lambda x: x['type'] == 'inetnum', data['objects']['object'])]
[{'inetnum': '77.88.55.0 - 77.88.55.255', 'netname': 'YANDEX-77-88-55', 'status': 'ASSIGNED PA', 'country': 'RU', 'descr': 'Yandex enterprise network', 'admin-c': 'YNDX1-RIPE', 'tech-c': 'YNDX1-RIPE', 'remarks': 'INFRA-AW', 'org': 'ORG-YA1-RIPE', 'mnt-by': 'YANDEX-MNT', 'source': 'RIPE', 'created': '2012-10-12T12:22:03Z', 'last-modified': '2022-04-05T15:29:50Z'}]
>>>

def ripe_search_inetnums(q):
  r = requests.get('https://rest.db.ripe.net/search.json', {'query-string': q, 'flags': 'no-filtering', 'type-filter': 'inetnum'})
  data = r.json()
  return [
    {x['name']: x['value'] for x in item['attributes']['attribute']}
    for item in filter(lambda x: x['type'] == 'inetnum', data['objects']['object'])
  ]

>>> results = ripe_search_inetnums('sberbank')
>>> len(results)
15
>>> results = ripe_search_inetnums('sber')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 6, in ripe_search_inetnums
KeyError: 'objects'
>>> results = ripe_search_inetnums('sber*')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 6, in ripe_search_inetnums
KeyError: 'objects'
```
</details>

Однако, позже я обнаружил эту ссылку https://apps.db.ripe.net/db-web-ui/fulltextsearch

API для вею-гуйни позволяет все-таки выполнять поиск по части имени:

```bash
curl -H'accept: application/json' 'https://apps.db.ripe.net/db-web-ui/api/rest/fulltextsearch/select?facet=true&format=xml&hl=true&q=(%22sber%22)%20AND%20(object-type:inetnum)&start=0&wt=json'
```

У них какой-то свой язык запросов:

```json
{
    "facet": "true",
    "format": "xml",
    "hl": "true",
    "q": "(\"sber\") AND (object-type:inet6num OR object-type:inetnum)",
    "start": "0",
    "wt": "json"
}
```

...но что сделано, то сделано, вернусь к этому проекту, если меня ripe.net забанит...

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

Параметр `q` поддерживает такие операторы как `-` (не включать сл слово) и `OR`. Данный функционал реализуется через `websearch_to_tsquery()`.

Мне лень расписывать все правила, поэтому я их спиздил [отсюда](https://docs.arenadata.io/ru/ADPG/current/how-to/queries/full-text-search.html).

`websearch_to_tsquery` использует альтернативный синтаксис для создания значения `tsquery` из текста запроса. Функция поддерживает следующий синтаксис:

* Текст без кавычек преобразуется в лексемы, разделенные оператором `&`.
* Текст в кавычках преобразуется в лексемы, разделенные оператором `<N>`.
* `OR` преобразуется в оператор `|`.
* `-` преобразуется в оператор `!`.

ссылки:

* [PostgreSQL: Full text search with the “websearch” syntax](https://adamj.eu/tech/2024/01/03/postgresql-full-text-search-websearch/)
* [Подробнее про tsquery](https://www.postgresql.org/docs/current/datatype-textsearch.html#DATATYPE-TSQUERY).

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

## TODO

* Кроме `org` есть еще поле `org-name`
