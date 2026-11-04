"""Complete published Server history before business schemas register."""

from __future__ import annotations

from contextlib import asynccontextmanager

from bazaar_contrib_schema import SCHEMA, ModuleSchema
from bazaar_core import Context, Contrib, ServiceKey

from .migrations import MODULE

__all__ = ["MODULE", "SERVER_MIGRATIONS", "migrations"]
SERVER_MIGRATIONS = ServiceKey[ModuleSchema]("server.migrations")


@asynccontextmanager
async def lifespan(ctx: Context):
    async with ctx.accept(SCHEMA).register(MODULE, upgrade_only=True):
        ctx.offer(SERVER_MIGRATIONS, MODULE)
        yield


migrations = Contrib(accepts=[SCHEMA], offers=[SERVER_MIGRATIONS], lifespan=lifespan)
