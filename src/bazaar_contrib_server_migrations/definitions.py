"""Server table and index definitions shared by upgrades and the current baseline."""

import bazaar_contrib_storage as s

ACCOUNTS_V1 = s.Table(
    name="accounts",
    columns=(
        s.ColumnDefinition(name="id", type="text", nullable=True),
        s.ColumnDefinition(name="name", type="text", unique=True),
        s.ColumnDefinition(name="password_hash", type="text"),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
        s.ColumnDefinition(name="language", type="text", nullable=True),
        s.ColumnDefinition(name="theme", type="text", nullable=True),
    ),
    primary_key=("id",),
)
COMPUTERS_V1 = s.Table(
    name="computers",
    columns=(
        s.ColumnDefinition(name="id", type="text", nullable=True),
        s.ColumnDefinition(name="name", type="text"),
        s.ColumnDefinition(name="secret_hash", type="text"),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
    ),
    primary_key=("id",),
)
EVENTS_V1 = s.Table(
    name="events",
    columns=(
        s.ColumnDefinition(name="id", type="integer", nullable=True, generated=True),
        s.ColumnDefinition(
            name="computer_id",
            type="text",
            references=s.Reference(table="computers", column="id"),
        ),
        s.ColumnDefinition(name="run_id", type="text"),
        s.ColumnDefinition(name="seq", type="integer"),
        s.ColumnDefinition(name="agent_id", type="text", nullable=True),
        s.ColumnDefinition(name="event_name", type="text"),
        s.ColumnDefinition(name="thread_id", type="text", nullable=True),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
        s.ColumnDefinition(name="received_at_ms", type="integer"),
        s.ColumnDefinition(name="payload", type="text"),
    ),
    primary_key=("id",),
    unique=(("computer_id", "run_id", "seq"),),
)
# the events held by their computer's id alone
EVENTS_V8 = s.Table(
    name="events",
    columns=(
        s.ColumnDefinition(name="id", type="integer", nullable=True, generated=True),
        s.ColumnDefinition(name="computer_id", type="text"),
        s.ColumnDefinition(name="run_id", type="text"),
        s.ColumnDefinition(name="seq", type="integer"),
        s.ColumnDefinition(name="agent_id", type="text", nullable=True),
        s.ColumnDefinition(name="event_name", type="text"),
        s.ColumnDefinition(name="thread_id", type="text", nullable=True),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
        s.ColumnDefinition(name="received_at_ms", type="integer"),
        s.ColumnDefinition(name="payload", type="text"),
    ),
    primary_key=("id",),
    unique=(("computer_id", "run_id", "seq"),),
)
EVENTS_BY_AGENT_V1 = s.Index(
    name="events_by_agent", columns=("computer_id", "agent_id", "id")
)
EVENTS_BY_NAME_V1 = s.Index(
    name="events_by_name", columns=("computer_id", "event_name", "agent_id", "id")
)
EVENTS_BY_THREAD_V1 = s.Index(
    name="events_by_thread",
    columns=("computer_id", "agent_id", "thread_id", "created_at_ms"),
)
RELATIONS_V1 = s.Table(
    name="relations",
    columns=(
        s.ColumnDefinition(name="subject_id", type="text"),
        s.ColumnDefinition(name="kind", type="text"),
        s.ColumnDefinition(name="target_id", type="text"),
        s.ColumnDefinition(name="ext", type="text", nullable=True),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
    ),
    primary_key=("subject_id", "kind", "target_id"),
)
RELATIONS_BY_TARGET_V1 = s.Index(
    name="relations_by_target", columns=("kind", "target_id")
)
REFS_V2 = s.Table(
    name="refs",
    columns=(
        s.ColumnDefinition(name="id", type="integer", nullable=True, generated=True),
        s.ColumnDefinition(name="value", type="text", unique=True),
    ),
    primary_key=("id",),
)
ROLES_V3 = s.Table(
    name="roles",
    columns=(
        s.ColumnDefinition(name="id", type="text", nullable=True),
        s.ColumnDefinition(name="name", type="text", unique=True),
        s.ColumnDefinition(name="permissions", type="text"),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
        s.ColumnDefinition(name="updated_at_ms", type="integer"),
    ),
    primary_key=("id",),
)
ACCOUNT_ROLES_V3 = s.Table(
    name="account_roles",
    columns=(
        s.ColumnDefinition(
            name="account_id",
            type="text",
            references=s.Reference(table="accounts", column="id", on_delete="cascade"),
        ),
        s.ColumnDefinition(
            name="role_id",
            type="text",
            references=s.Reference(table="roles", column="id", on_delete="cascade"),
        ),
    ),
    primary_key=("account_id", "role_id"),
)
ACCOUNT_ROLES_BY_ROLE_V3 = s.Index(name="account_roles_by_role", columns=("role_id",))
AUTH_SETTINGS_V3 = s.Table(
    name="auth_settings",
    columns=(
        s.ColumnDefinition(
            name="id",
            type="integer",
            nullable=True,
            generated=True,
            check=s.Compare(
                left=s.Column(name="id"), operator="=", right=s.Value(value=1)
            ),
        ),
        s.ColumnDefinition(
            name="default_role_id",
            type="text",
            nullable=True,
            references=s.Reference(table="roles", column="id"),
        ),
    ),
    primary_key=("id",),
)
OIDC_PROVIDERS_V3 = s.Table(
    name="oidc_providers",
    columns=(
        s.ColumnDefinition(name="id", type="text", nullable=True),
        s.ColumnDefinition(name="name", type="text"),
        s.ColumnDefinition(name="logo_url", type="text"),
        s.ColumnDefinition(name="issuer", type="text"),
        s.ColumnDefinition(name="client_id", type="text"),
        s.ColumnDefinition(name="client_secret", type="text"),
        s.ColumnDefinition(name="redirect_uri", type="text"),
        s.ColumnDefinition(name="created_at_ms", type="integer"),
        s.ColumnDefinition(name="updated_at_ms", type="integer"),
    ),
    primary_key=("id",),
)
OIDC_IDENTITIES_V3 = s.Table(
    name="oidc_identities",
    columns=(
        s.ColumnDefinition(name="issuer", type="text"),
        s.ColumnDefinition(name="subject", type="text"),
        s.ColumnDefinition(
            name="account_id",
            type="text",
            references=s.Reference(table="accounts", column="id", on_delete="cascade"),
        ),
        s.ColumnDefinition(
            name="provider_id",
            type="text",
            references=s.Reference(table="oidc_providers", column="id"),
        ),
        s.ColumnDefinition(name="display_name", type="text"),
        s.ColumnDefinition(name="email", type="text"),
    ),
    primary_key=("issuer", "subject"),
)
OIDC_IDENTITIES_BY_ACCOUNT_V3 = s.Index(
    name="oidc_identities_by_account", columns=("account_id",)
)
OIDC_TRANSACTIONS_V3 = s.Table(
    name="oidc_transactions",
    columns=(
        s.ColumnDefinition(name="state", type="text", nullable=True),
        s.ColumnDefinition(
            name="provider_id",
            type="text",
            references=s.Reference(
                table="oidc_providers", column="id", on_delete="cascade"
            ),
        ),
        s.ColumnDefinition(name="browser_hash", type="text"),
        s.ColumnDefinition(name="nonce", type="text"),
        s.ColumnDefinition(name="code_verifier", type="text"),
        s.ColumnDefinition(name="redirect_uri", type="text"),
        s.ColumnDefinition(name="expires_at_ms", type="integer"),
        s.ColumnDefinition(name="issuer", type="text", default=""),
        s.ColumnDefinition(name="subject", type="text", default=""),
    ),
    primary_key=("state",),
)
