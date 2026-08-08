#TypedDict State definition
from typing import TypedDict

#Define the state that will be used by the Agent.
class AgentState(TypedDict):
    user_input: str
    sql_query: str
    DB_answer: list
    final_answer: str
    maxIterations: int
    error_message: str
    schema: str
    