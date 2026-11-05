from __future__ import annotations

lazy import asyncio
lazy from collections.abc import AsyncIterator
lazy from contextlib import asynccontextmanager
lazy from pathlib import Path

import aiosqlite
from bazaar_core import ContribHub, ContribSpec, load

from bazaar_contrib_server_migrations import MODULE

PACKAGE = "bazaar-contrib-server-migrations"
NAME = "bcs.sqlite3"


@asynccontextmanager
async def migrated() -> AsyncIterator[None]:
    composition = await asyncio.to_thread(
        load,
        [
            ContribSpec(contrib=name, config=config)
            for name, config in (
                ("timer-wheel", {}),
                ("server-database", {}),
                ("server-migrations", {}),
            )
        ],
    )
    async with ContribHub() as hub, hub.enable(composition):
        yield


async def restore(path: Path, version: int) -> None:
    fixtures = (await asyncio.to_thread(Path(__file__).resolve)).parent / "fixtures"
    dump = await asyncio.to_thread((fixtures / f"server-v{version}.sql").read_text)
    await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as connection:
        await connection.executescript(dump)


async def query(path: Path, sql: str, *parameters: object) -> list[tuple[object, ...]]:
    async with (
        aiosqlite.connect(path) as connection,
        connection.execute(sql, parameters) as cursor,
    ):
        return [tuple(row) for row in await cursor.fetchall()]


async def tables(path: Path) -> set[str]:
    rows = await query(path, "SELECT name FROM sqlite_master WHERE type = 'table'")
    return {str(row[0]) for row in rows}


async def versions(path: Path) -> list[tuple[object, ...]]:
    return await query(
        path,
        "SELECT version, name FROM contrib_schema_migrations WHERE package = ?",
        PACKAGE,
    )


async def test_a_published_database_reaches_version_7_with_its_data_and_ledger(
    tmp_path: Path,
):
    path = tmp_path / ".bcn" / NAME
    expected = tmp_path / "expected.sqlite3"
    await restore(path, 3)
    await restore(expected, 7)
    original = await query(path, "SELECT * FROM schema_migrations")
    async with migrated():
        pass
    published = await tables(expected)
    # the original ledger stays as it was published and is compared below
    for table in sorted(set(MODULE.tables) & published - {"schema_migrations"}):
        rows = await query(path, f'SELECT * FROM "{table}"')
        assert sorted(map(repr, rows)) == sorted(
            map(repr, await query(expected, f'SELECT * FROM "{table}"'))
        ), table
    assert await query(path, "SELECT * FROM schema_migrations") == original
    assert max(int(str(version)) for version, _ in await versions(path)) == (
        MODULE.version
    )


async def test_a_fresh_database_is_left_to_the_modules_that_own_the_tables(
    tmp_path: Path,
):
    async with migrated():
        pass
    path = tmp_path / ".bcn" / NAME
    assert not set(MODULE.tables) & await tables(path)
    assert not await versions(path)


async def test_restarting_on_a_current_database_repeats_nothing(tmp_path: Path):
    path = tmp_path / ".bcn" / NAME
    await restore(path, 7)
    async with migrated():
        pass
    history = await versions(path)
    computers = await query(path, "SELECT * FROM computers")
    async with migrated():
        pass
    assert await versions(path) == history
    assert await query(path, "SELECT * FROM computers") == computers
