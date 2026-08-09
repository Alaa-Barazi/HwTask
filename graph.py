from sqlalchemy import Engine, create_engine
from dataBaseTool import DataBaseTool
from schemaRetreivalTool import SchemaTool
from agentNode import AgentNode
from state import AgentState
from langgraph.graph import StateGraph, START, END
from llm_client import LLMClient
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))  # from .env
db_tool = DataBaseTool(engine=engine)
schema_tool = SchemaTool(engine=engine)


agent_node = agent_node = AgentNode(llm_client=LLMClient())

#Build the graph nodes
def agent_build_node(state: AgentState) -> dict:
    return agent_node.build_query(state, state["user_input"])

def schema_node(engine: Engine) -> dict:
    return schema_tool.get_schema_for_state()

def agent_node_fn(state: AgentState) -> dict:
    # A DB attempt was made and succeeded (no error) — summarize, even if empty.
    if state.get("sql_query") and state.get("error_message") in (None, ""):
        if state.get("DB_answer") is not None and state.get("DB_answer") != "":
            return agent_node.generate_final_answer(state)

    # Iteration budget exhausted — stop with whatever explanation we have.
    if state.get("maxIterations", 1) <= 0:
        message = state.get("error_message") or "Max iterations reached without a result."
        return {"final_answer": f"I couldn't complete this request: {message}"}

    # A previous attempt errored (bad SQL, non-read-only, DB exception) — retry.
    if state.get("error_message"):
        retry_state = {**state, "sql_query": ""}  # clear so build_query regenerates
        result = agent_node.build_query(retry_state, state["user_input"])
      
        return result

    # Default: no query yet, build one.
    result = agent_node.build_query(state, state["user_input"])

    return result




def db_node(state: AgentState) -> dict:
    return db_tool.execute_sql(state["sql_query"])

def final_answer_node(state: AgentState) -> dict:
    return agent_node.generate_final_answer(state)




graph = StateGraph(AgentState)
graph.add_node("agent", agent_build_node)
graph.add_node("schema_tool", schema_node)
graph.add_node("db_tool", db_node)
graph.add_node("final_answer", final_answer_node)



def route_from_agent(state: AgentState) -> str:
    if state.get("final_answer"):
        return END
    if state.get("sql_query") and not state.get("DB_answer") and not state.get("error_message"):
        return "db_tool"
    if state.get("error_message"):
        return "agent"  # error path: build_query will already have retried above
    return "agent"  # safety fallback; shouldn't normally be hit
 


#Build the graph
graph = StateGraph(AgentState)
graph.add_node("schema_tool", schema_node)
graph.add_node("agent", agent_node_fn)
graph.add_node("db_tool", db_node)

graph.add_edge(START, "schema_tool")
graph.add_edge("schema_tool", "agent")
graph.add_conditional_edges("agent", route_from_agent, {
    "db_tool": "db_tool",
    "agent": "agent",
    END: END,
})
graph.add_edge("db_tool", "agent")

app = graph.compile()

def ask(question: str) -> str:
    initial_state: AgentState = {
        "user_input": question,
        "sql_query": "",
        "DB_answer": "",
        "final_answer": "",
        "maxIterations": 5,
        "error_message": "",
        "error_type": "",
        "schema": "",
    }
    result = app.invoke(initial_state)
    return result["final_answer"]