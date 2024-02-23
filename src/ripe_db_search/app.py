import asyncio
import ipaddress
import logging
import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Literal,
    TypeVar,
)

import asyncpg
from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from pydantic import (
    BaseModel,
    Field,
    IPvAnyAddress,
    IPvAnyNetwork,
    computed_field,
)

from .config import settings

LOG = logging.getLogger("uvicorn.error")
CUR_PATH = Path(__file__).parent
DB_SCHEMA_PATH = CUR_PATH / "schema.sql"

# NOT_FOUND_EXCEPTION = HTTPException(404, detail={"message": "Object Not Found"})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = app.pool = await asyncpg.create_pool(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_pass,
        port=settings.db_port,
    )
    if DB_SCHEMA_PATH.exists():
        await pool.execute(DB_SCHEMA_PATH.read_text())
    yield
    await pool.close()


# >>> socket.gethostbyname('ya.ru')
# '77.88.55.242'
async def gethostbyname(host: str, port: int = 0) -> str:
    result = await asyncio.get_running_loop().getaddrinfo(
        host, port, family=socket.AF_UNSPEC
    )
    return result[0][4][0]


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_execution_time_header(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    dt = -time.monotonic()
    response = await call_next(request)
    dt += time.monotonic()
    response.headers["X-Execution-Time"] = str(dt)
    return response


class Inetnum(BaseModel):
    first_ip: IPvAnyAddress
    last_ip: IPvAnyAddress
    netname: str | None = None
    descr: str | None = None
    country: str | None = None
    org: str | None = None
    mnt_by: str | None = None
    admin_c: str | None = None
    tech_c: str | None = None
    notify: str | None = None
    source: str | None = None
    status: str | None = None
    created: datetime | None = None
    last_modified: datetime | None = None

    @computed_field
    @property
    def cidrs(self) -> list[IPvAnyNetwork]:
        return list(
            ipaddress.summarize_address_range(self.first_ip, self.last_ip)
        )

    @computed_field
    @property
    def num_addresses(self) -> int:
        return sum(x.num_addresses for x in self.cidrs)


class IPInfo(BaseModel):
    input: str
    ip: str
    inetnum: Inetnum


@app.get("/ipinfo/{addr}", response_model_exclude_none=True)
async def ipinfo(addr: str) -> IPInfo:
    try:
        async with asyncio.timeout(2):
            ip = await gethostbyname(addr)
            LOG.info("resolved: %s -> %s", addr, ip)
    except (socket.gaierror, TimeoutError):
        raise HTTPException(
            400, detail={"message": "invalid address or timeout"}
        )
    # В базе данных RIPE много записей с пересекающимися диапазонами, мы ищем наименьший диапазон. Если ничего подходящего не будет найдено, то вернет что-то типа 0.0.0.0-255.255.255.255
    record = await app.pool.fetchrow(
        """
        select * from inetnums
            where $1 between first_ip and last_ip
            order by first_ip desc, last_ip asc
            limit 1
        """,
        ip,
    )
    return dict(input=addr, ip=ip, inetnum=Inetnum(**record))


# https://docs.pydantic.dev/latest/concepts/models/#generic-models
T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    page: int
    per_page: int
    total: int
    results: list[T]

    @computed_field
    @property
    def pages(self) -> int:
        return self.total // self.per_page + 1


class SearchParams(BaseModel):
    q: str = ""
    page: int = Field(1, alias="p", ge=1)
    # приводит к ошибке
    # per_page: Literal[10, 25, 50, 100, 250, 500] = 25
    per_page: int = Field(25, ge=1, le=500)


@app.get("/search", response_model_exclude_none=True)
async def search(s: SearchParams = Depends()) -> Pagination[Inetnum]:
    # Тут мы одним запросом возвращаем записи с их общим количеством, но стоит
    # только добавить order by как все начинает тормозить...
    # TODO: пофиксить
    records = list(
        await app.pool.fetch(
            """
            select *, count(*) over() as total_count from inetnums
                where search_vector @@ websearch_to_tsquery($1)
                limit $2 offset $3
            """,
            s.q,
            s.per_page,
            (s.page - 1) * s.per_page,
        )
    )
    return {
        "page": s.page,
        "per_page": s.per_page,
        "total": records[0]["total_count"] if records else 0,
        "results": [Inetnum(**x) for x in records],
    }
