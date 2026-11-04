from __future__ import annotations

from contextlib import asynccontextmanager
lazy import asyncio
lazy from pathlib import Path

import aiosqlite
from bazaar_contrib_collaboration import COLLABORATION
from bazaar_contrib_storage import DB, Database, Insert, Select
from bazaar_core import Context, Contrib, ContribEntry, ContribHub, ContribSpec, load

from bazaar_contrib_server_migrations import SERVER_MIGRATIONS


async def test_business_roots_select_only_their_migration_plugin(tmp_path: Path):
    services: list[Database] = []
    selected = tmp_path / ".bcn" / "selected.sqlite3"
    # Server tables come from a published database; fresh ones belong to the
    # modules that own them
    fixtures = (await asyncio.to_thread(Path(__file__).resolve)).parent / "fixtures"
    dump = await asyncio.to_thread((fixtures / "server-v3.sql").read_text)
    await asyncio.to_thread(selected.parent.mkdir, parents=True, exist_ok=True)
    async with aiosqlite.connect(selected) as connection:
        await connection.executescript(dump)

    @asynccontextmanager
    async def node_consumer(ctx: Context):
        ctx.accept(COLLABORATION)
        db = ctx.accept(DB)
        services.append(db)
        await db.insert(
            Insert(
                table="settings",
                rows=(
                    {
                        "agent_id": "agent",
                        "key": "welcome",
                        "value": "Ready after Node migration",
                        "updated_at_ms": 1,
                    },
                ),
            )
        )
        yield

    @asynccontextmanager
    async def server_consumer(ctx: Context):
        ctx.accept(SERVER_MIGRATIONS)
        db = ctx.accept(DB)
        services.append(db)
        await db.insert(
            Insert(
                table="computers",
                rows=(
                    {
                        "id": "enrolled",
                        "name": "Ready after Server migration",
                        "secret_hash": "test-only",
                        "created_at_ms": 1,
                    },
                ),
            )
        )
        yield

    composition = await asyncio.to_thread(
        load,
        [
            ContribSpec(contrib=name, config=config)
            for name, config in (
                ("storage", {}),
                ("sqlite", {"name": selected.name}),
                ("database", {"backend": "sqlite"}),
                ("schema", {}),
                ("legacy-node-migrations", {}),
                ("audit", {}),
                ("timer-wheel", {}),
                ("messages-node", {}),
                ("collaboration", {}),
                ("server-migrations", {}),
            )
        ],
    )
    composition = composition.model_copy(
        update={
            "entries": (
                *composition.entries,
                ContribEntry(
                    name="node",
                    definition=Contrib(
                        accepts=[DB, COLLABORATION], lifespan=node_consumer
                    ),
                ),
                ContribEntry(
                    name="server",
                    definition=Contrib(
                        accepts=[DB, SERVER_MIGRATIONS], lifespan=server_consumer
                    ),
                ),
            ),
            "roots": ("node",),
        }
    )
    async with ContribHub() as hub, hub.enable(composition) as enabled:
        assert (await services[-1].select(Select(table="settings")))[0][
            "value"
        ] == "Ready after Node migration"
        await enabled.update(composition.model_copy(update={"roots": ("server",)}))
        computers = await services[-1].select(Select(table="computers"))
        assert "Ready after Server migration" in {row["name"] for row in computers}
        assert (await services[-1].select(Select(table="settings")))[0][
            "value"
        ] == "Ready after Node migration"
