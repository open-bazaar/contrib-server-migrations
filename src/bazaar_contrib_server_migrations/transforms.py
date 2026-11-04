"""Historical authentication data transformations through public storage."""

from __future__ import annotations

lazy import json

import bazaar_contrib_storage as s


async def login_order(session: s.Session) -> None:
    providers = await session.select(
        s.Select(
            table="oidc_providers",
            columns={"id": s.Column(name="id")},
            order_by=(
                s.Sort(expression=s.Column(name="created_at_ms")),
                s.Sort(expression=s.Column(name="id")),
            ),
        )
    )
    await session.update(
        s.Update(
            table="auth_settings",
            values={
                "login_order": s.Value(
                    value=json.dumps(
                        ["password", *(row["id"] for row in providers)],
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                )
            },
            where=s.Compare(
                left=s.Column(name="id"), operator="=", right=s.Value(value=1)
            ),
        )
    )
