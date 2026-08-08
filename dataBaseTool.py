import re
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result
""" Logic for the engne in main: shared_engine = create_engine(connection_string)
db_tool = DataBaseTool(engine=shared_engine)
schema = get_schema_metadata(shared_engine)"""
class DataBaseTool:
    """

    The APIs in this class do not store state on the instance; instead, every
    execution method accepts the current query as a parameter
    and returns a fresh dict rather than touching any external state object.
    """
 
    def __init__(self, engine: Engine):
        if engine is not None:
            self.engine = engine
       

    def execute_sql(self, sql:str) -> Dict[str, Any]:
        """Execute the SQL stored in the passed state. """
        if sql is None or sql == "":
           
            return {"error_message": "No SQL query was found in state.", "DB_answer": []}

        try:
            self._assert_read_only_sql(sql)

            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                rows = self._result_to_rows(result)

            # if not rows:
            #     raise RuntimeError("The SQL executed successfully, but it returned no rows.")

      
            return {"DB_answer": rows, "error_message": None}

        except Exception as exc:
       
            return {"DB_answer": [], "error_message": str(exc)}


    

    def _assert_read_only_sql(self, sql: str) -> None:
        """Read-only compliance check that runs in Python before hitting the DB.

        The SQL must begin with a SELECT and must not contain write statements.
        This prevents write-like SQL from ever reaching SQLAlchemy/DB engine.
        """
        cleaned = self._strip_sql_comments(sql)
        cleaned = cleaned.strip()

        if not cleaned:
            raise ValueError("Empty SQL query.")

        # Allow SQL that starts with SELECT immediately. SQLAlchemy text() can
        # handle whitespace and trailing semicolons safely.
        if not re.match(r"^\s*SELECT\b", cleaned, flags=re.IGNORECASE):
            raise ValueError(
                "Read-only violation: only SELECT queries are permitted. "
                "Write statements are rejected before execution."
            )

        write_like_tokens = (
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "REPLACE",
            "MERGE",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
            "CALL",
            "EXEC",
            "EXECUTE",
            "COPY",
        )

        for token in write_like_tokens:
            if re.search(rf"\b{token}\b", cleaned, flags=re.IGNORECASE):
                raise ValueError(
                    f"Read-only violation: write statement token '{token}' detected before execution."
                )

    def _strip_sql_comments(self, sql: str) -> str:
        """Remove single-line and block comments so checks are not fooled by them."""
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
        sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
        return sql

    def _result_to_rows(self, result: Result) -> list:
        """Normalize SQLAlchemy result rows into a portable list-of-dict format."""
        rows = []
        try:
            columns = list(result.keys())
        except Exception:
            columns = []

        for row in result:
            if hasattr(row, "_mapping"):
                rows.append(dict(row._mapping))
            else:
                rows.append(dict(zip(columns, row)))

        return rows
