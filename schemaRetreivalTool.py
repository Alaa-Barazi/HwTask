from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def get_schema_metadata(engine: Engine) -> Dict[str, Any]:
    """
    Deterministic SQLAlchemy schema introspection.

    Does not use an LLM — calls SQLAlchemy's inspect() API to reflect the
    database schema at runtime: table names, columns, types, nullability,
    primary keys, and foreign keys. No caching here; caching is handled by
    SchemaTool, scoped to however long that instance is kept alive.

    Args:
        engine: A SQLAlchemy Engine instance (SQLite, MySQL, Postgres, etc.)

    Returns:
        A dictionary describing the schema.
    """
    if engine is None:
        raise ValueError("A SQLAlchemy Engine instance is required.")

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    schema: Dict[str, Any] = {
        "database": {
            "dialect": engine.dialect.name,
            "url": str(engine.url),
        },
        "tables": [],
    }

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        primary_key = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)

        column_payload: List[Dict[str, Any]] = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column.get("nullable", True),
                "default": column.get("default"),
                "autoincrement": column.get("autoincrement"),
                "comment": column.get("comment"),
            }
            for column in columns
        ]

        schema["tables"].append(
            {
                "name": table_name,
                "columns": column_payload,
                "primary_key": {
                    "name": primary_key.get("name"),
                    "columns": primary_key.get("constrained_columns", []),
                },
                "foreign_keys": [
                    {
                        "name": fk.get("name"),
                        "constrained_columns": fk.get("constrained_columns", []),
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns", []),
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {
                        "name": idx.get("name"),
                        "columns": idx.get("column_names", []),
                        "unique": idx.get("unique", False),
                    }
                    for idx in indexes
                ],
            }
        )

    return schema


def get_schema_text(engine: Engine) -> str:
    """Convenience formatter: turns schema metadata into a plain-text
    description suitable for prompt injection or logging."""
    schema = get_schema_metadata(engine)
    lines: List[str] = []

    for table in schema["tables"]:
        lines.append(f"Table: {table['name']}")
        for column in table["columns"]:
            lines.append(
                f"  - {column['name']}: {column['type']}"
                f" (nullable={column['nullable']})"
            )
        if table["foreign_keys"]:
            lines.append("  Foreign Keys:")
            for fk in table["foreign_keys"]:
                cols = ", ".join(fk["constrained_columns"])
                ref_cols = ", ".join(fk["referred_columns"])
                lines.append(
                    f"    - {cols} -> {fk['referred_table']}({ref_cols})"
                )
        lines.append("")

    return "\n".join(lines)

class SchemaTool:
    """Deterministic, non-LLM schema introspection with per-instance caching.

    Cache lifetime is tied to however long this object is kept alive by the
    caller (e.g., one instance per conversation/session) — not global to the
    whole process, so separate sessions never share or leak cached schema.
    """

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._cache: Optional[str] = None

    def get_schema_for_state(self) -> Dict[str, str]:
        """Entry point for graph wiring: returns a partial state update
        with the schema already formatted as the string AgentState expects.
        """
        if self._cache is None:
            self._cache = get_schema_text(self.engine)
        return {"schema": self._cache}

    def clear_cache(self) -> None:
        """Optional helper for tests or explicit reset scenarios."""
        self._cache = None