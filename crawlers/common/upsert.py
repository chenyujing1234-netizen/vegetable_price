"""通用的 PostgreSQL upsert 工具，避免每次重写 ON CONFLICT 语句"""

from typing import Iterable

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


def upsert_many(
    session: Session,
    table: Table,
    rows: Iterable[dict],
    conflict_columns: list[str],
    update_columns: list[str] | None = None,
) -> int:
    rows = list(rows)
    if not rows:
        return 0
    stmt = insert(table).values(rows)
    update_set = {c: getattr(stmt.excluded, c) for c in (update_columns or [])}
    if update_set:
        stmt = stmt.on_conflict_do_update(index_elements=conflict_columns, set_=update_set)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)
    session.execute(stmt)
    return len(rows)
