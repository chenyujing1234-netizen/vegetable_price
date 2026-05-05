"""爬虫使用的同步数据库连接工厂

爬虫为单进程批处理任务，使用同步 SQLAlchemy 比异步更简单可靠。
"""

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql+psycopg://veg:vegpass@localhost:5432/vegdb",
)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
