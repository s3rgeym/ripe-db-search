#!/usr/bin/env python
# https://habr.com/ru/companies/Linx/articles/526508/
# https://habr.com/ru/articles/554458/
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


class ANSI:
    CSI = "\x1b["
    RESET = f"{CSI}m"
    CLEAR_LINE = f"{CSI}2K\r"
    BLACK = f"{CSI}30m"
    ERROR = WARNING = RED = f"{CSI}31m"
    SUCCESS = OK = GREEN = f"{CSI}32m"
    ORANGE = YELLOW = f"{CSI}33m"
    BLUE = f"{CSI}34m"
    PURPLE = MAGENTA = f"{CSI}35m"
    CYAN = f"{CSI}36m"
    GREY = WHITE = f"{CSI}37m"


CUR_PATH = Path(__file__).parent

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
    skip_download_if_exists: bool


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
    parser.add_argument(
        "--skip-download-if-exists",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="skip download if file exists",
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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.7",
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
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w+b") as fp:
            shutil.copyfileobj(resp, fp)


def parse_block(curline: str, fp: TextIO) -> dict[str, str]:
    rv = {}
    while curline := curline.strip():
        try:
            # https://datatracker.ietf.org/doc/html/rfc2622#section-2
            try:
                #  An RPSL object is textually represented as a list of attribute-value
                # pairs.  Each attribute-value pair is written on a separate line.  The
                # attribute name starts at column 0, followed by character ":" and
                # followed by the value of the attribute.
                key, value = curline.split(":", 1)
            except ValueError:
                # Там в базах всякий мусор лежит
                continue
            # An object's description may contain comments.  A comment can be
            # anywhere in an object's definition, it starts at the first "#"
            # character on a line and ends at the first end-of-line character.
            # White space characters can be used to improve readability.
            value = value.split("#")[0].strip()
            if key in rv:
                # Правильно бы было загнать все в массив, но пока это излишне
                rv[key] += " " + value
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
                # if block.get("status") == "LEGACY":
                #     continue
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


def normalize_inetnums(
    batch: tuple[InetnumDict | Ine6tnumDict, ...]
) -> Iterable[tuple]:
    for item in batch:
        try:
            first_ip, last_ip = get_first_and_last_ips(
                item["inet6num"] if "inet6num" in item else item["inetnum"]
            )
        # FIXME: ValueError: 24.152.0/22
        except ValueError as ex:
            # print_stderr(f"{ANSI.RED}WARN: {ex}{ANSI.RESET}")
            continue
        netname = item.get("netname")
        description = item.get("descr")
        organization = item.get("org")
        country = item.get("country")
        mnt_by = item.get("mnt-by")
        # admin_c = item.get("admin-c")
        # tech_c = item.get("tech-c")

        # Почта админа подсети
        notify = item.get("notify")
        # Содержит имя базы, но нужно ли оно? - Думаю, что нет, но пусть будет
        # select string_agg(distinct(source),',') from inetnums;
        # Ripe, APNiC, 'RIPE'
        source = item.get("source")
        status = item.get("status")
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
            description,
            organization,
            country,
            mnt_by,
            # admin_c,
            # tech_c,
            notify,
            source,
            status,
            created,
            last_modified,
        )


# https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
# https://en.wikipedia.org/wiki/Braille_pattern_dots-12356
def spinner() -> Iterable[str]:
    while 42:
        # yield from "⣾⣽⣻⢿⡿⣟⣯⣷"
        yield from "⠾⠽⠻⠟⠯⠷"


async def main(argv: Sequence[str] | None = None) -> None:
    parser, args = parse_args(argv=argv)
    total_time = -time.monotonic()

    database_paths = {
        url: DATABASE_DIR_PATH / filename_from_url(url) for url in DATABASE_URLS
    }

    for url, path in database_paths.items():
        print_stderr(f"{ANSI.YELLOW}downloading {url}{ANSI.RESET}", end="")
        if path.exists() and args.skip_download_if_exists:
            print_stderr(
                f"{ANSI.CLEAR_LINE}{ANSI.MAGENTA}already downloaded: {url}{ANSI.RESET}"
            )
            continue
        try:
            download_database(url, path)
            print_stderr(
                f"{ANSI.CLEAR_LINE}{ANSI.GREEN}downloaded: {url}{ANSI.RESET}"
            )
        except urllib.error.URLError as ex:
            if getattr(ex, "code") != 304:
                print_stderr(
                    f"{ANSI.CLEAR_LINE}{ANSI.RED}error: {ex}{ANSI.RESET}"
                )
                sys.exit(1)
            print_stderr(
                f"{ANSI.CLEAR_LINE}{ANSI.MAGENTA}resource is not modified: {url}{ANSI.RESET}"
            )

    spin = spinner()
    total_records = 0
    async with get_connection(args) as con:
        # try:
        #     import ripe_db_search

        #     schema_path = Path(ripe_db_search.__file__).parent
        # except ImportError:
        #     schema_path = CUR_PATH / "src" / "ripe_db_search"

        schema_path = CUR_PATH / "src" / "ripe_db_search"
        schema_path /= "schema.sql"

        if schema_path.exists():
            await con.execute(schema_path.read_text())

        await con.execute(
            "TRUNCATE inetnums; ALTER SEQUENCE inetnums_id_seq RESTART WITH 1"
        )

        print_stderr(f"{ANSI.YELLOW}start importing{path}{ANSI.RESET}", end="")

        for path in database_paths.values():
            print_stderr(
                f"{ANSI.CLEAR_LINE}{ANSI.YELLOW}import {path}{ANSI.RESET}"
            )
            # База большая и вставлять по одной записи очень долго
            for batch in itertools.batched(
                parse_database(path),
                args.batch_size,
            ):
                async with con.transaction():
                    status = await con.copy_records_to_table(
                        "inetnums",
                        records=normalize_inetnums(batch),
                        columns=(
                            "first_ip",
                            "last_ip",
                            "netname",
                            "descr",
                            "org",
                            "country",
                            "mnt_by",
                            # "admin_c",
                            # "tech_c",
                            "notify",
                            "source",
                            "status",
                            "created",
                            "last_modified",
                        ),
                    )
                    # 'COPY 1024'
                    op, size = status.split()
                    assert op == "COPY", op
                    total_records += int(size)
                    print_stderr(
                        f"{ANSI.CLEAR_LINE}{ANSI.YELLOW}{next(spin)} total records copied: {total_records}{ANSI.RESET}",
                        end="",
                    )
        print_stderr()
    total_time += time.monotonic()
    print_stderr(f"{ANSI.GREEN}finished at {total_time:.3f}s{ANSI.RESET}")


if __name__ == "__main__":
    load_dotenv()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
