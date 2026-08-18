import asyncio
import os
from typing import TypedDict, Annotated
import operator
import uuid

import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,   
)
from langchain_groq import ChatGroq
#from tools.tavily_tool import tavily_search
from mcp_client import tavily_mcp_search
from tools.flight_tool import search_flights

from dotenv import load_dotenv
load_dotenv()

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile"
)

DATABASE_URL = os.getenv("DATABASE_URL")

# State definition
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int

# 1. Flight Agent Node
def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)
    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content="Flight results fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# 2. Hotel Agent Node
def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    #hotel_results = tavily_search(query)
    hotel_results = asyncio.run(tavily_mcp_search(query))
    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# 3. Itinerary Agent Node
def itinerary_agent(state: TravelState):
    prompt = f"""
    Create a travel itinerary.
    User Query : {state['user_query']}
    Flight_results : {state['flight_results']} 
    hotel_results: {state['hotel_results']}
    """
   
    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner"),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

# 4. Final Agent Node
def final_agent(state: TravelState):
    final_prompt = f""" Generate final travel response.
    flights : {state["flight_results"]}
    hotels : {state["hotel_results"]}
    itinerary : {state['itinerary']}
    """

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

# Create graph at the global module level (not inside itinerary_agent)
# Note: '# type: ignore' silences the false positive warning from Pyrefly/Pyright
graph = StateGraph(TravelState)  # type: ignore

# Add nodes
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

# Add edges
graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)

# Compile app with Postgres checkpointer, fallback to MemorySaver if unavailable
if DATABASE_URL:
    try:
        # autocommit=True and row_factory=dict_row are required by PostgresSaver
        _conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True)
        checkpointer = PostgresSaver(_conn)
        checkpointer.setup()
        app = graph.compile(checkpointer=checkpointer)
    except Exception as e:
        print(f"Warning: PostgreSQL Saver connection failed: {e}. Falling back to MemorySaver.")
        from langgraph.checkpoint.memory import MemorySaver
        app = graph.compile(checkpointer=MemorySaver())
else:
    from langgraph.checkpoint.memory import MemorySaver
    app = graph.compile(checkpointer=MemorySaver())


    

if __name__ == "__main__":
    test_query = "Plan a 3-day trip to Paris"
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())}
    }

    for chunk in app.stream(
        {
            "messages": [HumanMessage(content=test_query)],
            "user_query": test_query,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    ):
        print(chunk)
