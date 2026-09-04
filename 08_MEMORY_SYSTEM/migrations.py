"""
Schema migration runner (spec 8.7: "database implementation replaceable
through an upper-layer repository contract").

Each migration is ``(version, sql_statements)``. ``apply`` is idempotent:
it tracks the applied version in a ``schema_version`` table and only
runs migrations above the current version.
"""

MIGRATIONS = [
    (
        1,
        [
            """
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                user_scope TEXT NOT NULL,
                namespace TEXT,
                type TEXT NOT NULL,
                content TEXT,
                metadata TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                expires_at TEXT
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(user_scope)",
            "CREATE INDEX IF NOT EXISTS idx_memories_namespace ON memories(namespace)",
        ],
    ),
]


class Migrations:
    VERSION = MIGRATIONS[-1][0]

    def current(self):
        return self.VERSION

    def apply(self, connection):
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
        )
        row = connection.execute("SELECT MAX(version) FROM schema_version").fetchone()
        applied = row[0] if row and row[0] is not None else 0

        for version, statements in MIGRATIONS:
            if version <= applied:
                continue
            for statement in statements:
                connection.execute(statement)
            connection.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))
        connection.commit()
        return self.VERSION
