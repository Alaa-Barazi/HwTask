from __future__ import annotations

from typing import Any

from state import AgentState


class AgentNode:
    """Node responsible for receiving the user's natural language question and deciding
    what the next step should be in the agent pipeline.

    Behavior:
    - If the schema has not been fetched yet, request the schema.
    - If the schema is available but no SQL query exists yet, generate a SQL query.
    - Once query results are available, produce the final human-readable answer.

    This node is the only place that calls the LLM.

    Stateless by design: every method receives the current AgentState explicitly
    and returns only the fields it changed. The graph (or its checkpointer) owns
    state persistence across calls — nothing is cached on the instance.
    """

    def __init__(self, llm_client: Any) -> None:
        self.llm_client = llm_client

    def build_query(self, state: AgentState, user_question: str) -> AgentState:
        """Decide the next action based on the current conversation state."""

        if not state.get("schema"):
            return {
                "error_message": "Schema not yet fetched; routing to schema tool.",
            }

        if state.get("maxIterations") is not None and state.get("maxIterations", 1) == 0:
            return {
                "error_message": "Maximum number of iterations reached; stopping execution.",
            }

        if not state.get("sql_query"):
            sql_query = self.llm_client.generate_sql(
                question=user_question,
                schema=state.get("schema"),
            )
            return {"sql_query": sql_query, "error_message": None}

        # Both schema and query exist — nothing new to decide here;
        # routing should send this case to the DB tool.
        return {"error_message": None}

    def execute_query(self, state: AgentState, db_tool: Any) -> AgentState:
        """Validate the query is read-only, execute it, and report results or errors."""

        sql_query = state.get("sql_query")
        if not sql_query:
            return {"error_message": "No SQL query to execute."}

        if not sql_query.strip().lower().startswith("select"):
            return {"error_message": "Only read-only queries are allowed."}

        try:
            db_result = db_tool.execute(sql_query)
            updated_iterations = state.get("maxIterations", 1) - 1
            return {
                "DB_answer": db_result,
                "maxIterations": updated_iterations,
                "error_message": None,
            }
        except Exception as e:
            return {"error_message": f"Database execution error: {str(e)}"}

    def generate_final_answer(self, state: AgentState) -> AgentState:
        """Turn the DB result into a human-readable answer, or surface a pending error."""

        error_message = state.get("error_message")
        if error_message:
            return {"error_message": error_message}

        sql_query = state.get("sql_query")
        db_answer = state.get("DB_answer")
        if not sql_query or db_answer is None:
            return {"error_message": "Cannot generate final answer without SQL query and DB answer."}

        final_answer = self.llm_client.generate_final_answer(
            question=state.get("user_input"),
            sql_query=sql_query,
            db_answer=db_answer,
        )
        return {"final_answer": final_answer}
