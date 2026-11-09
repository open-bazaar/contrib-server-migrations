"""Business-owned schema evolution through the public migration contract."""

from __future__ import annotations

import bazaar_contrib_storage as s
from bazaar_contrib_schema import Migration, ModuleSchema, Progress

from . import definitions, transforms


async def roles_oidc(session: s.Session) -> None:
    await session.apply_schema(
        (
            s.AddColumn(
                table="accounts",
                column=s.ColumnDefinition(
                    name="auth_type", type="text", default="local"
                ),
            ),
            s.AddColumn(
                table="accounts",
                column=s.ColumnDefinition(
                    name="session_version", type="integer", default=0
                ),
            ),
            s.CreateTable(table=definitions.ROLES_V3),
            s.CreateTable(table=definitions.ACCOUNT_ROLES_V3),
            s.CreateIndex(
                table="account_roles", index=definitions.ACCOUNT_ROLES_BY_ROLE_V3
            ),
            s.CreateTable(table=definitions.AUTH_SETTINGS_V3),
        )
    )
    await session.insert(s.Insert(table="auth_settings", rows=({"id": 1},)))
    await session.apply_schema(
        (
            s.CreateTable(table=definitions.OIDC_PROVIDERS_V3),
            s.CreateTable(table=definitions.OIDC_IDENTITIES_V3),
            s.CreateIndex(
                table="oidc_identities", index=definitions.OIDC_IDENTITIES_BY_ACCOUNT_V3
            ),
            s.CreateTable(table=definitions.OIDC_TRANSACTIONS_V3),
            s.CreateIndex(
                table="oidc_transactions",
                index=s.Index(
                    name="oidc_transactions_by_expiry", columns=("expires_at_ms",)
                ),
            ),
        )
    )


async def login_order(session: s.Session) -> None:
    await session.apply_schema(
        (
            s.AddColumn(
                table="auth_settings",
                column=s.ColumnDefinition(
                    name="login_order", type="text", default='["password"]'
                ),
            ),
        )
    )
    await transforms.login_order(session)


async def events_by_id(session: s.Session) -> None:
    """The events let go of their computer: a computer is removed without
    first removing what it reported, which the module holding the events
    removes itself; every row and index stays as it was, and the ids go on
    above the highest the events ever had."""
    indexes = (
        definitions.EVENTS_BY_AGENT_V1,
        definitions.EVENTS_BY_NAME_V1,
        definitions.EVENTS_BY_THREAD_V1,
    )
    # the highest id ever given, which SQLite keeps beside the table and the
    # rows left may fall short of; the rebuilt table starts without it
    given = await session.select(
        s.Select(
            table="sqlite_sequence",
            columns={"seq": s.Column(name="seq")},
            where=s.Compare(
                left=s.Column(name="name"), operator="=", right=s.Value(value="events")
            ),
        )
    )
    await session.apply_schema(
        (
            *(s.DropIndex(table="events", name=index.name) for index in indexes),
            s.RenameTable(table="events", name="_events_v7"),
            s.CreateTable(table=definitions.EVENTS_V8),
        )
    )
    if given:
        # a row at that id, taken away again, leaves it recorded for the new table
        await session.insert(
            s.Insert(
                table="events",
                rows=(
                    {
                        "id": given[0]["seq"],
                        "computer_id": "",
                        "run_id": "",
                        "seq": 0,
                        "event_name": "",
                        "created_at_ms": 0,
                        "received_at_ms": 0,
                        "payload": "",
                    },
                ),
            )
        )
        await session.delete(
            s.Delete(
                table="events",
                where=s.Compare(
                    left=s.Column(name="id"),
                    operator="=",
                    right=s.Value(value=given[0]["seq"]),
                ),
            )
        )
    await session.copy(
        s.Copy(
            table="events",
            query=s.Select(
                table="_events_v7",
                columns={
                    column.name: s.Column(name=column.name)
                    for column in definitions.EVENTS_V8.columns
                },
            ),
        )
    )
    await session.apply_schema(
        (
            s.DropTable(table="_events_v7"),
            *(s.CreateIndex(table="events", index=index) for index in indexes),
        )
    )


MODULE = ModuleSchema(
    tables=(
        "account_roles",
        "accounts",
        "auth_settings",
        "computers",
        "events",
        "_events_v7",
        "oidc_identities",
        "oidc_providers",
        "oidc_transactions",
        "refs",
        "relations",
        "roles",
        "schema_migrations",
    ),
    progress=Progress(table="schema_migrations", identity="initial_server_schema"),
    migrations=(
        Migration(
            version=1,
            name="initial_server_schema",
            operations=(
                s.CreateTable(table=definitions.ACCOUNTS_V1),
                s.CreateTable(table=definitions.COMPUTERS_V1),
                s.CreateTable(table=definitions.EVENTS_V1),
                s.CreateIndex(table="events", index=definitions.EVENTS_BY_AGENT_V1),
                s.CreateIndex(table="events", index=definitions.EVENTS_BY_NAME_V1),
                s.CreateIndex(table="events", index=definitions.EVENTS_BY_THREAD_V1),
                s.CreateTable(table=definitions.RELATIONS_V1),
                s.CreateIndex(
                    table="relations", index=definitions.RELATIONS_BY_TARGET_V1
                ),
            ),
        ),
        Migration(
            version=2,
            name="refs",
            operations=(s.CreateTable(table=definitions.REFS_V2),),
        ),
        Migration(version=3, name="roles_oidc", apply=roles_oidc),
        Migration(version=4, name="login_order", apply=login_order),
        Migration(
            version=5,
            name="provider_description",
            operations=(
                s.AddColumn(
                    table="oidc_providers",
                    column=s.ColumnDefinition(
                        name="description", type="text", default=""
                    ),
                ),
            ),
        ),
        Migration(
            version=6,
            name="provider_default_role",
            operations=(
                s.AddColumn(
                    table="oidc_providers",
                    column=s.ColumnDefinition(
                        name="default_role_id",
                        type="text",
                        nullable=True,
                        references=s.Reference(table="roles", column="id"),
                    ),
                ),
            ),
        ),
        Migration(
            version=7,
            name="oidc_session_settings",
            operations=(
                s.AddColumn(
                    table="oidc_providers",
                    column=s.ColumnDefinition(
                        name="session_minutes", type="integer", default=10
                    ),
                ),
                s.DropTable(table="oidc_transactions"),
            ),
        ),
        Migration(version=8, name="events_by_id", apply=events_by_id),
    ),
)
