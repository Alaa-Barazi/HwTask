from __future__ import annotations

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()


class LLMClient:
    """Thin wrapper around ChatAnthropic exposing exactly the two operations
    AgentNode needs: SQL generation and final-answer summarization.
    """

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment.")
        self.llm = ChatAnthropic(model=model, api_key=api_key)

    def generate_sql(self, question: str, schema: str) -> str:
        prompt = (
            
            f"You are a SQL generator. Given this database schema:\n{schema}\n\n"
            f"IMPORTANT: If multiple tables share similarly-named columns (e.g., a 'Name' "
            f"column appearing in more than one table), use the table and column "
            f"relationships (foreign keys) described in the schema, and the context of the "
            f"question itself, to determine which table a referenced entity belongs to. "
            f"Do not default to the first matching table without considering context.\n\n"
            f"Write a single read-only SQL SELECT query to answer this question:\n"
            f"{question}\n\n"
            f"Return only the SQL query, no explanation."

        )
        
        response = self.llm.invoke(prompt)
        sql = response.content.strip()
    # Strip markdown code fences in case the LLM wraps its answer despite instructions
        if sql.startswith("```"):
            sql = sql.strip("`")
            if sql.lower().startswith("sql"):
                sql = sql[3:].strip()
        return sql
     

    def generate_final_answer(self, question: str, sql_query: str, db_answer: str) -> str:
        prompt = (
              f"The user asked: {question}\n"
            f"This SQL query was run: {sql_query}\n"
            f"The database returned: {db_answer}\n\n"
            f"Write a concise, direct answer to the user's question based on this data. "
            f"Use a table if there are multiple rows/columns, otherwise a short sentence. "
            f"Do not add a summary, restatement, or extra commentary beyond directly "
            f"answering what was asked."
        )
        response = self.llm.invoke(prompt)
        return response.content.strip()