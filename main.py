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

from mcp_client import (
    tavily_mcp_search,
     get_airports ,
      get_airlines,
      aviation_mcp_call,
      weather_mcp_search,
      forecast_mcp_search,
      extract_destination)



from dotenv import load_dotenv
load_dotenv()

# Initialize LLM
llm = ChatGroq(
    model="qwen/qwen3.6-27b"
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
    weather_results: str
    

# 1. Flight Agent Node

FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""



def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:1000],
            airline_data=str(airlines)[:1000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt)
        ])

        flight_data = response.content

    except Exception as e:

        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
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

def weather_agent(state: TravelState):

    city = extract_destination(state["user_query"])

    weather_data = asyncio.run(
        weather_mcp_search(city)
    )

    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )

    return {
        "weather_results": f"""
        Current Weather:
        {weather_data}

        Forecast:
        {forecast_data}
        """,
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ]
    }

# 3. Itinerary Agent Node
def itinerary_agent(state: TravelState):
    print("=== DEBUG ITINERARY AGENT ===")
    print(f"flight_results len: {len(str(state.get('flight_results')))}")
    print(f"hotel_results len: {len(str(state.get('hotel_results')))}")
    print(f"weather_results len: {len(str(state.get('weather_results')))}")
    
    prompt = f"""
    Create a travel itinerary.
    User Query : {state['user_query']}
    Flight_results : {str(state['flight_results'])[:1000]} 
    hotel_results: {str(state['hotel_results'])[:1000]}
    weather_results: {str(state['weather_results'])[:1000]}
    """
    print(f"Constructed prompt len: {len(prompt)}")
    print("=============================")

    try:
        response = llm.invoke([
            SystemMessage(content="You are an expert travel planner"),
            HumanMessage(content=prompt)
        ])
        itinerary_data = response.content
        msg = response
    except Exception as e:
        print(f"ERROR calling LLM in itinerary_agent: {e}")
        itinerary_data = f"Itinerary generation failed: {str(e)}"
        msg = AIMessage(content=itinerary_data)
   
    return {
        "itinerary": itinerary_data,
        "messages": [msg],
        "llm_calls": state.get('llm_calls', 0) + 1
    }





# Create graph at the global module level (not inside itinerary_agent)
# Note: '# type: ignore' silences the false positive warning from Pyrefly/Pyright
graph = StateGraph(TravelState)  # type: ignore

# Add nodes
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)


# Add edges
graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "weather_agent")
graph.add_edge("weather_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", END)

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
