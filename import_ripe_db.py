#!/usr/bin/env python
# @link https://habr.com/ru/companies/Linx/articles/526508/
import argparse
import asyncio
import functools
import gzip
import ipaddress
import itertools
import shutil
import sys
import time
import urllib.error
from contextlib import asynccontextmanager
from datetime import datetime
from os import getenv
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Iterable,
    Literal,
    NotRequired,
    Sequence,
    TextIO,
    TypedDict,
)
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import asyncpg
from dotenv import load_dotenv

__version__ = "0.1.0"

CLEAR = "\x1b[m"
BLACK = "\x1b[30m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
WHITE = "\x1b[37m"
CLEAR_LINE = "\x1b[2K\r"

# Latest Chrome UA 18/02/2024
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/121.0.0.0 Safari/537.36"
)


DATABASE_URLS = [
    "https://ftp.ripe.net/ripe/dbase/split/ripe.db.inetnum.gz",
    "https://ftp.ripe.net/ripe/dbase/split/ripe.db.inet6num.gz",
    # нигры
    "https://ftp.afrinic.net/pub/dbase/afrinic.db.gz",
    # азиатско-тихоокеанский регион (восточная азия, австралия и океания)
    "https://ftp.apnic.net/pub/apnic/whois/apnic.db.inetnum.gz",
    "https://ftp.apnic.net/pub/apnic/whois/apnic.db.inet6num.gz",
    # северная америка
    # по всей видимости ничего нужного не содержит:
    # $ curl -s https://ftp.arin.net/pub/rr/arin.db.gz | zgrep -E 'inet6?num'
    "https://ftp.arin.net/pub/rr/arin.db.gz",
    # латинская америка
    "https://ftp.lacnic.net/lacnic/dbase/lacnic.db.gz",
]

DATABASE_DIR_PATH = Path(__file__).parent / "ripe"

print_stderr = functools.partial(print, file=sys.stderr)


class NameSpace(argparse.Namespace):
    dsn: str | None
    host: str | None
    port: int | None
    user: str | None
    password: str | None
    dbname: str | None
    batch_size: int


def parse_args(
    argv: Sequence[str] | None,
) -> tuple[argparse.ArgumentParser, NameSpace]:
    parser = argparse.ArgumentParser(
        description="Import Ripe DB into PostgreSQL"
    )
    parser.add_argument("--dsn", help="database uri")
    parser.add_argument("-H", "--host", help="database host")
    parser.add_argument("-p", "--port", type=int, help="database port")
    parser.add_argument("-u", "--user", help="database user")
    parser.add_argument("-P", "--password", help="database password")
    parser.add_argument("-d", "--dbname", help="database name")
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=8192,
        help="batch size for inserting records into the database",
    )
    return parser, parser.parse_args(argv, namespace=NameSpace())


# Все поля кроме inetnum/inet6num опциональны, хотя whois показывает, что netname оьязательный, но в базе есть записи без него!

# ❯ whois -t inetnum
# % This is the RIPE Database query service.
# % The objects are in RPSL format.
# %
# % The RIPE Database is subject to Terms and Conditions.
# % See https://apps.db.ripe.net/docs/HTML-Terms-And-Conditions

# inetnum:        [mandatory]  [single]     [primary/lookup key]
# netname:        [mandatory]  [single]     [lookup key]
# descr:          [optional]   [multiple]   [ ]
# country:        [mandatory]  [multiple]   [ ]
# geofeed:        [optional]   [single]     [ ]
# geoloc:         [optional]   [single]     [ ]
# language:       [optional]   [multiple]   [ ]
# org:            [optional]   [single]     [inverse key]
# sponsoring-org: [optional]   [single]     [ ]
# admin-c:        [mandatory]  [multiple]   [inverse key]
# tech-c:         [mandatory]  [multiple]   [inverse key]
# abuse-c:        [optional]   [single]     [inverse key]
# status:         [mandatory]  [single]     [ ]
# remarks:        [optional]   [multiple]   [ ]
# notify:         [optional]   [multiple]   [inverse key]
# mnt-by:         [mandatory]  [multiple]   [inverse key]
# mnt-lower:      [optional]   [multiple]   [inverse key]
# mnt-domains:    [optional]   [multiple]   [inverse key]
# mnt-routes:     [optional]   [multiple]   [inverse key]
# mnt-irt:        [optional]   [multiple]   [inverse key]
# created:        [generated]  [single]     [ ]
# last-modified:  [generated]  [single]     [ ]
# source:         [mandatory]  [single]     [ ]

# % This query was served by the RIPE Database Query Service version 1.109.1 (BUSA)

_InetnumDict = TypedDict(
    "_InetnumDict",
    {
        "language": NotRequired[str],
        "mnt-irt": NotRequired[str],
        "created": NotRequired[str],
        "admin-c": NotRequired[str],
        "assignment-size": NotRequired[str],
        "netname": NotRequired[str],
        "website-if-available": NotRequired[str],
        "sponsoring-org": NotRequired[str],
        "mnt-lower": NotRequired[str],
        "org": NotRequired[str],
        "organisation-location": NotRequired[str],
        "remarks": NotRequired[str],
        "mnt-routes": NotRequired[str],
        "geoloc": NotRequired[str],
        "descr": NotRequired[str],
        "mnt-by": NotRequired[str],
        "tech-c": NotRequired[str],
        "last-modified": NotRequired[str],
        "country": NotRequired[str],
        "mnt-domains": NotRequired[str],
        "source": NotRequired[str],
        "notify": NotRequired[str],
        "abuse-c": NotRequired[str],
        "geofeed": NotRequired[str],
        "status": NotRequired[str],
    },
)


# pylint: disable=E0239
class InetnumDict(_InetnumDict):
    inetnum: str


class Ine6tnumDict(_InetnumDict):
    inet6num: str


# pylint: enable=E0239


def filename_from_url(url: str) -> str:
    return Path(urlparse(url).path).name


def download_database(
    url: str,
    path: Path,
) -> None:
    headers = {
        "User-Agent": USER_AGENT,
    }
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Modified-Since
    if path.exists():
        # Я подозреваю, что сервер ripe.net не поддерживает этот заголовок
        timestamp = path.stat().st_mtime
        # {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36', 'If-modified-since': 'Tue, 20 Feb 2024 22:18:46 GMT'}
        headers |= {
            "If-Modified-Since": time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp)
            )
        }

    req = Request(url, headers=headers)

    with urlopen(req) as resp:
        with path.open("w+b") as fp:
            shutil.copyfileobj(resp, fp)


def parse_block(curline: str, fp: TextIO) -> dict[str, str]:
    rv = {}
    while curline := curline.strip():
        try:
            try:
                key, value = curline.split(":", 1)
            except ValueError:
                continue
            value = value.lstrip()
            if key in rv:
                rv[key] += "\n" + value
            else:
                rv[key] = value
        finally:
            curline = next(fp, "")
    return rv


def parse_database(path: Path) -> Iterable[dict]:
    with gzip.open(path, "rt", errors="replace") as fp:
        for line in fp:
            # # https://apps.db.ripe.net/docs/RPSL-Object-Types/Descriptions-of-Primary-Objects/
            # Тип объекта - первая строка
            if line.startswith(("inetnum", "inet6num")):
                block = parse_block(line, fp)
                # All the legacy objects will have the status ‘LEGACY'.
                if block.get("status") == "LEGACY":
                    continue
                yield block


@asynccontextmanager
async def get_connection(args: NameSpace) -> AsyncIterator[asyncpg.Connection]:
    conn: asyncpg.Connection
    # all is none
    if not any(
        (
            args.dsn,
            args.host,
            args.port,
            args.user,
            args.password,
            args.dbname,
        )
    ):
        con = await asyncpg.connect(
            host=getenv("DB_HOST"),
            port=int(getenv("DB_PORT", 5432)),
            user=getenv("DB_USER"),
            password=getenv("DB_PASS"),
            database=getenv("DB_NAME"),
        )
    else:
        con = await asyncpg.connect(
            dsn=args.dsn,
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.dbname,
        )
    try:
        yield con
    finally:
        await con.close()


def get_first_and_last_ips(
    s: str,
) -> (
    tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]
    | tuple[ipaddress.IPv6Address, ipaddress.IPv6Address]
):
    try:
        n = ipaddress.ip_network(s)
        return n[0], n[-1]
    except ValueError:
        pass
    try:
        first, last = map(ipaddress.ip_address, map(str.strip, s.split("-")))
        return first, last
    except ValueError:
        pass
    raise ValueError(s)


def normalize_batch(
    batch: tuple[InetnumDict | Ine6tnumDict, ...]
) -> Iterable[tuple]:
    for item in batch:
        try:
            first_ip, last_ip = get_first_and_last_ips(
                item["inet6num"] if "inet6num" in item else item["inetnum"]
            )
        # FIXME: ValueError: 24.152.0/22
        except ValueError as ex:
            continue
        netname = item.get("netname")
        descr = item.get("descr")
        org = item.get("org")
        if country := item.get("country"):
            # fix: "EU # Country is really world wide"
            country, *_ = country.split()
        created, last_modified = (
            (
                datetime.fromisoformat(item[i]).replace(tzinfo=None)
                if i in item
                else None
            )
            for i in ("created", "last-modified")
        )
        yield (
            first_ip,
            last_ip,
            netname,
            descr,
            org,
            country,
            created,
            last_modified,
        )


def spinner() -> Iterable[Literal["|", "/", "-", "\\"]]:
    while 42:
        yield from "|/-\\"


async def main(argv: Sequence[str] | None = None) -> None:
    parser, args = parse_args(argv=argv)
    total_time = -time.monotonic()

    database_paths = {
        url: DATABASE_DIR_PATH / filename_from_url(url) for url in DATABASE_URLS
    }

    print_stderr(f"{YELLOW}downloading...{CLEAR}")
    for url, path in database_paths.items():
        try:
            download_database(url, path)
            print_stderr(f"{GREEN}downloaded: {url}{CLEAR}")
        except urllib.error.URLError as ex:
            if getattr(ex, "code") != 304:
                print_stderr(f"{RED}{ex}{CLEAR}")
                sys.exit(1)
            print_stderr(f"{MAGENTA}resource is not modified: {url}{CLEAR}")

    spin = spinner()
    total_records = 0
    async with get_connection(args) as con:
        await con.execute("TRUNCATE inetnums")
        for path in database_paths.values():
            print_stderr(f"{CLEAR_LINE}{YELLOW}import {path}{CLEAR}", end="")
            # База большая и вставлять по одной записи очень долго
            for batch in itertools.batched(
                parse_database(path),
                args.batch_size,
            ):
                async with con.transaction():
                    status = await con.copy_records_to_table(
                        "inetnums",
                        records=normalize_batch(batch),
                        columns=(
                            "first_ip",
                            "last_ip",
                            "netname",
                            "descr",
                            "org",
                            "country",
                            "created",
                            "last_modified",
                        ),
                    )
                    # 'COPY 1024'
                    op, size = status.split()
                    assert op == "COPY", op
                    total_records += int(size)
                    print_stderr(
                        f"{CLEAR_LINE}{YELLOW}{next(spin)} total records copied: {total_records}{CLEAR}",
                        end="",
                    )
        print_stderr()
    total_time += time.monotonic()
    print_stderr(f"{GREEN}finished at {total_time:.3f}s{CLEAR}")


if __name__ == "__main__":
    load_dotenv()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
