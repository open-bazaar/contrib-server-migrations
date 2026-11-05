# bazaar-contrib-server-migrations

Upgrade existing Server databases through the published migrations 1–7; fresh databases use the baselines of the modules that own the tables. The history registers on `SERVER_SCHEMA`, the schema of the server's own database from `bazaar-contrib-server-database`.

```sh
bcn contrib add server-migrations --enable
```

The corresponding entry in `config.toml`:

```toml
version = "5"

[[contribs]]
package = "bazaar-contrib-server-migrations==0.3.*"
[[contribs.enabled]]
entry = "server-migrations"
```

A module that takes over a Server table accepts `SERVER_MIGRATIONS`, registers on `SERVER_SCHEMA` and declares `bazaar-contrib-server-migrations` version 7 as the predecessor of its own schema.
