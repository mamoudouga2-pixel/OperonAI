"""
SQLite-backed structured persistent storage (spec 8.7).

This is the reference/local implementation. Anything above the
Repository layer must not depend on SQLite-specific behaviour, so a
Postgres/other adapter can be dropped in later.
"""

import json
import sqlite3

from errors import StructuredStoreUnavailable
from .migrations import Migrations


class SQLiteAdapter:
    def __init__(self, path=":memory:"):
        self.path = path
        try:
            self.db = sqlite3.connect(path, check_same_thread=False)
        except sqlite3.Error as exc:
            raise StructuredStoreUnavailable(str(exc)) from exc
        Migrations().apply(self.db)

    def health_check(self):
        try:
            self.db.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def upsert(self, memory):
        try:
            self.db.execute(
                """
                INSERT INTO memories
                    (memory_id, user_scope, namespace, type, content, metadata,
                     created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    user_scope=excluded.user_scope,
                    namespace=excluded.namespace,
                    type=excluded.type,
                    content=excluded.content,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at,
                    expires_at=excluded.expires_at
                """,
                (
                    memory["memory_id"],
                    memory.get("user_scope"),
                    memory.get("namespace"),
                    memory.get("type"),
                    json.dumps(memory.get("content")),
                    json.dumps(memory),
                    memory.get("created_at"),
                    memory.get("updated_at"),
                    memory.get("expires_at"),
                ),
            )
            self.db.commit()
        except sqlite3.Error as exc:
            raise StructuredStoreUnavailable(str(exc)) from exc
        return memory

    def get(self, memory_id):
        row = self.db.execute(
            "SELECT metadata FROM memories WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, memory_id):
        self.db.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        self.db.commit()

    def search(self, scope, namespace=None):
        query = "SELECT metadata FROM memories WHERE user_scope = ?"
        args = [scope]
        if namespace:
            query += " AND namespace = ?"
            args.append(namespace)
        return [json.loads(row[0]) for row in self.db.execute(query, args)]

    def all_ids(self, scope=None):
        if scope is None:
            rows = self.db.execute("SELECT memory_id FROM memories")
        else:
            rows = self.db.execute(
                "SELECT memory_id FROM memories WHERE user_scope = ?", (scope,)
            )
        return [row[0] for row in rows]

    def snapshot(self):
        return [
            json.loads(row[0]) for row in self.db.execute("SELECT metadata FROM memories")
        ]

    def restore(self, records):
        for record in records:
            self.upsert(record)

    def close(self):
        self.db.close()
