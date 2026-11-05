from __future__ import annotations

from contextlib import asynccontextmanager
lazy import asyncio
lazy from pathlib import Path

import aiosqlite
from bazaar_contrib_collaboration import COLLABORATION
from bazaar_contrib_server_database import SERVER_DB
from bazaar_contrib_storage import DB, Database, Insert, Select
from bazaar_core import Context, Contrib, ContribEntry, ContribHub, ContribSpec, load

from bazaar_contrib_server_migrations import SERVER_MIGRATIONS


async def test_the_node_and_the_server_migrate_their_own_databases(tmp_path: Path):
    databases: dict[str, Database] = {}
    published = tmp_path / ".bcn" / "bcs.sqlite3"
    # The server continues a published database; the node starts its own
    fixtures = (await asyncio.to_thread(Path(__file__).resolve)).parent / "fixtures"
    dump = await asyncio.to_thread((fixtures / "server-v3.sql").read_text)
    await asyncio.to_thread(published.parent.mkdir, parents=True, exist_ok=True)
    async with aiosqlite.connect(published) as connection:
        await connection.executescript(dump)

    @asynccontextmanager
    async def node_consumer(ctx: Context):
        ctx.accept(COLLABORATION)
        db = ctx.accept(DB)
        databases["node"] = db
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
        db = ctx.accept(SERVER_DB)
        databases["server"] = db
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
                ("sqlite", {}),
                ("database", {"backend": "sqlite"}),
                ("schema", {}),
                ("legacy-node-migrations", {}),
                ("audit", {}),
                ("timer-wheel", {}),
                ("messages-node", {}),
                ("collaboration", {}),
                ("server-database", {}),
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
                        accepts=[SERVER_DB, SERVER_MIGRATIONS], lifespan=server_consumer
                    ),
                ),
            )
        }
    )
    async with ContribHub() as hub, hub.enable(composition):
        settings = await databases["node"].select(Select(table="settings"))
        assert "Ready after Node migration" in {row["value"] for row in settings}
        computers = await databases["server"].select(Select(table="computers"))
        assert "Ready after Server migration" in {row["name"] for row in computers}
        assert not await databases["node"].table_exists("computers")
        assert not await databases["server"].table_exists("settings")
