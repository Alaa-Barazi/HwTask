# test_agent.py
from unittest import result

from langgraph.graph import END

import pytest
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

from dataBaseTool import DataBaseTool
from schemaRetreivalTool import SchemaTool

from graph import app 
from graph import route_from_agent
load_dotenv()


@pytest.fixture(scope="module")
def engine():
    return create_engine(os.getenv("DATABASE_URL"))


@pytest.fixture(scope="module")
def db_tool(engine):
    return DataBaseTool(engine=engine)


def make_initial_state(question: str) -> dict:
    return {
        "user_input": question,
        "sql_query": "",
        "DB_answer": "",
        "final_answer": "",
        "maxIterations": 5,
        "error_message": "",
        "schema": "",
    }


# ---------- Deterministic, no-LLM tests (fill these in) ----------

def test_read_only_check_rejects_delete(db_tool):
    result = db_tool.execute_sql("DELETE FROM coursegrade WHERE StudentID = 1;")
    
    # TODO: assert error_message is set, DB_answer is empty/unset
    assert result.get("error_message") is not None 
    assert result.get("DB_answer") == []


def test_read_only_check_accepts_select(db_tool):
    result = db_tool.execute_sql("SELECT * FROM teacher;")
    # TODO: assert error_message is None, DB_answer has rows
    assert isinstance(result.get("DB_answer"), list)
    assert len(result["DB_answer"]) > 0


def test_route_from_agent_branches():
    

    # Query ready, no DB_answer yet, no error -> should go to db_tool
    state_ready_to_execute = make_initial_state("dummy")
    state_ready_to_execute["sql_query"] = "SELECT * FROM teacher;"
    assert route_from_agent(state_ready_to_execute) == "db_tool"

    # Final answer already produced -> should end
    state_done = make_initial_state("dummy")
    state_done["final_answer"] = "Some answer"
    assert route_from_agent(state_done) == END  # import END from langgraph.graph in this file


# ---------- End-to-end tests (real LLM + real DB) ----------

def test_end_to_end_simple_query():
    state = make_initial_state("What courses have only 3 points?")
    result = app.invoke(state)
    assert result.get("final_answer")
    assert "Databases" in result["final_answer"] 
    assert "Web" in result["final_answer"]  


def test_end_to_end_join_query():
    state = make_initial_state("What courses did Bob take in Winter 2026?")
    result = app.invoke(state)
    assert result.get("final_answer")
    # No Winter semester exists in seed data -> expect a graceful "no results" answer,
    # not a crash and not fabricated course names
    assert result.get("error_message") in (None, "")


def test_end_to_end_no_matching_entity():
    state = make_initial_state("What is the average grade for John?")
    result = app.invoke(state)
    assert result.get("final_answer")
    assert result.get("error_message") in (None, "")


def test_end_to_end_out_of_schema_question():
    state = make_initial_state("What are the cheapest hotels in Spain?")
    result = app.invoke(state)
    assert result.get("final_answer")
    assert "€" not in result["final_answer"] and "$" not in result["final_answer"]