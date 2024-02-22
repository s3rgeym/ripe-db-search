import asyncio
import ipaddress
import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, Generic, TypeVar

import asyncpg
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, IPvAnyAddress, IPvAnyNetwork, computed_field

from .config import settings

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
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    dt = -time.monotonic()
    response = await call_next(request)
    dt += time.monotonic()
    response.headers["X-Execution-Time"] = str(dt)
    return response


class InetnumModel(BaseModel):
    first_ip: IPvAnyAddress
    last_ip: IPvAnyAddress
    netname: str | None
    descr: str | None
    country: str | None
    org: str | None
    created: datetime | None
    last_modified: datetime | None

    @computed_field
    @property
    def cidrs(self) -> list[IPvAnyNetwork]:
        return list(
            ipaddress.summarize_address_range(self.first_ip, self.last_ip)
        )


class IPInfoModel(BaseModel):
    input: str
    ip: str
    inetnum: InetnumModel


@app.get("/addrinfo/{addr}")
async def ipinfo(addr: str) -> IPInfoModel:
    try:
        ip = await gethostbyname(addr)
    except socket.gaierror:
        raise HTTPException(400, detail={"message": "invalid address"})
    # В базе данных RIPE много записей с пересекающимися диапазонами
    # select * from inetnums where '77.88.55.242' between first_ip and last_ip order by 1 desc limit 1;
    record = await app.pool.fetchrow(
        "select * from inetnums where $1 between first_ip and last_ip order by first_ip desc, last_ip asc",
        ip,
    )
    return dict(input=addr, ip=ip, inetnum=InetnumModel(**record))


# https://docs.pydantic.dev/latest/concepts/models/#generic-models
T = TypeVar("T")


class PageModel(BaseModel, Generic[T]):
    page: int
    per_page: int
    pages: int
    total: int
    results: list[T]


@app.get("/search")
async def search(
    q: str, page: int = 1, per_page: int = 100
) -> PageModel[InetnumModel]:
    page = max(page, 1)
    per_page = min(500, max(per_page, 10))
    limit = page * per_page
    offset = limit - per_page
    records = [
        record
        for record in await app.pool.fetch(
            "select *, count(*) over() as total_count from inetnums where search_vector @@ to_tsquery($1) order by id desc limit $2 offset $3",
            q,
            limit,
            offset,
        )
    ]
    total = records[0]["total_count"] if records else 0
    return {
        "page": page,
        "per_page": per_page,
        "pages": total // per_page + 1,
        "total": total,
        "results": [InetnumModel(**x) for x in records],
    }
