import asyncio
import json
import re
from typing import Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.types import interrupt
from config import get_llm
from mcp_client import (
    current_weather, forecast, list_airlines, list_airports, tavily_search
)
from state import TravelState

llm = get_llm()

def _llm_text(system: str, prompt: str) -> str:
    response = llm.invoke([
        SystemMessage(
            content=system
        ),
        HumanMessage(
            content=prompt
        )
    ])
    # Strip <think>...</think> blocks from text response content if present
    clean_content = re.sub(r"<think>.*?</think>", "", response.content, flags=re.DOTALL).strip()
    return clean_content

def _json_from_llm(text: str) -> dict:
    print("\n========== RAW LLM RESPONSE ==========")
    print(text)
    print("======================================\n")

    # 1. Remove <think>...</think> blocks if present
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # 2. Try to find json inside markdown code blocks
    # Try ```json ... ``` first
    json_blocks = re.findall(r"```json\s*(.*?)\s*```", clean_text, flags=re.DOTALL)
    if json_blocks:
        for block in json_blocks:
            try:
                parsed = json.loads(block.strip())
                print("\n========== EXTRACTED JSON (from ```json block) ==========")
                print(block.strip())
                print("=========================================================\n")
                return parsed
            except json.JSONDecodeError:
                continue

    # Try general ``` ... ``` code blocks
    code_blocks = re.findall(r"```\s*(.*?)\s*```", clean_text, flags=re.DOTALL)
    if code_blocks:
        for block in code_blocks:
            try:
                parsed = json.loads(block.strip())
                print("\n========== EXTRACTED JSON (from ``` block) ==========")
                print(block.strip())
                print("====================================================\n")
                return parsed
            except json.JSONDecodeError:
                continue

    # 3. Fall back to finding the first { and last }
    try:
        start = clean_text.index("{")
        end = clean_text.rindex("}") + 1
        json_text = clean_text[start:end]
        
        print("\n========== EXTRACTED JSON (fallback) ==========")
        print(json_text)
        print("================================================\n")
        return json.loads(json_text)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error extracting JSON using fallback: {e}")
        # If all else fails, try loading the clean_text as is
        return json.loads(clean_text)

def supervisor_agent(state: TravelState):
    query = state["user_query"]
            
    # INPUT GUARDRAIL
    guardrail_prompt = f"""
    Determine whether the following request is a valid travel planning request.

    Return only JSON in this format:

    {{
        "allowed": true,
        "reason": ""
    }}

    User request:
    {query}
    """

    guardrail_raw = _llm_text(
        "You are an input validation guardrail. Return strict JSON only.",
        guardrail_prompt,
    )

    print("\n========== GUARDRAIL RAW RESPONSE ==========")
    print(guardrail_raw)
    print("============================================\n")

    guardrail_result = _json_from_llm(guardrail_raw)

    print("\n========== GUARDRAIL PARSED RESPONSE ==========")
    print(json.dumps(guardrail_result, indent=2))
    print("================================================\n")

    if not guardrail_result.get("allowed", False):
        reason = guardrail_result.get(
            "reason",
            "Request rejected by input guardrail."
        )

        return {
            "selected_agents": [],
            "trip_constraints": {},
            "supervisor_reasoning": reason,
            "final_response": reason,
            "messages": [
                AIMessage(content=f"Guardrail blocked request: {reason}")
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }


    # supervisor logic is starting from here:
    existing_constraints = state.get("trip_constraints", {})
    context_str = ""
    if existing_constraints:
        context_str = f"\nPrevious Trip Context:\n{json.dumps(existing_constraints, indent=2)}\n"

    prompt = f"""
You are the supervisor of a real-world multi-agent travel planning system.

Decide which specialist agents are needed for this user request.

Available agents:
- flight_agent: use when flights, airports, airlines, routes, or airfare guidance are needed
- hotel_agent: use when hotels, stays, neighborhoods, or accommodation are needed
- weather_agent: use when weather, climate, season, packing, or forecast is useful
- budget_agent: use when budget, affordability, cost, or price constraints are mentioned
- itinerary_agent: almost always needed to produce the travel plan

Return only JSON with this schema:
{{
  "selected_agents": ["flight_agent", "hotel_agent", "weather_agent", "budget_agent", "itinerary_agent"],
  "trip_constraints": {{
    "destination": "",
    "origin": "",
    "duration": "",
    "budget": "",
    "travel_style": "",
    "special_preferences": []
  }},
  "reasoning": ""
}}
{context_str}
User request (could be a follow-up or adjustment to previous trip):
{query}
"""

 
    raw = _llm_text(
        "You route work to specialist agents. Return strict JSON only.",
        prompt,
    )

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw)
    print("======================================\n")

    parsed = _json_from_llm(raw)
   
    #parsed = json.loads(raw)
    
    print("\n========== PARSED JSON ==========")
    print(json.dumps(parsed, indent=2))
    print("=================================\n")
    
    '''
    At first glance they look the same, but they're not:

    raw → string returned by the LLM
    parsed → Python dictionary created from that string

    If you really want to demonstrate the difference, add:

    print(type(raw))
    print(type(parsed))
    Output:

    <class 'str'>
    <class 'dict'>
    Yes, you can get output from a string, but it's much harder and less reliable.
    '''
    
    selected = parsed["selected_agents"]    

    # Merge new constraints with existing ones, preserving previous values if new ones are empty
    merged_constraints = {}
    new_constraints = parsed.get("trip_constraints", {})
    for k in ["destination", "origin", "duration", "budget", "travel_style", "special_preferences"]:
        old_val = existing_constraints.get(k)
        new_val = new_constraints.get(k)
        if new_val and (not isinstance(new_val, list) or len(new_val) > 0):
            merged_constraints[k] = new_val
        else:
            merged_constraints[k] = old_val if old_val is not None else ([] if k == "special_preferences" else "")

    return {
        "selected_agents": selected,
        "trip_constraints": merged_constraints,
        "supervisor_reasoning": parsed["reasoning"],
        "messages": [AIMessage(content="Supervisor created the agent plan.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }



def flight_agent(state: TravelState):
    query = state["user_query"]
    constraints = state["trip_constraints"]
    destination = constraints["destination"]

    print("\n========== FLIGHT AGENT INPUT ==========")
    print("Query:", query)
    print("Constraints:", constraints)
    print("========================================\n")

    airports = asyncio.run(list_airports(destination, limit=10))
    airlines = asyncio.run(list_airlines("", limit=10))

    print("\n========== AIRPORT MCP DATA ==========")
    print(airports)
    print("======================================\n")

    print("\n========== AIRLINE MCP DATA ==========")
    print(airlines)
    print("======================================\n")

    prompt = f"""
Create highly concise flight guidance for this trip.
Keep your output short (max 150 words).

User request:
{query}

Trip constraints:
{constraints}

Airport MCP data:
{str(airports)[:1500]}

Airline MCP data:
{str(airlines)[:1500]}

Include departure/arrival airports, key airlines, estimated duration, fare range, and one quick booking tip.
"""

    result = _llm_text(
        "You are a flight planning specialist.",
        prompt,
    )

    print("\n========== FLIGHT AGENT OUTPUT ==========")
    print(result)
    print("=========================================\n")

    return {
        "flight_results": result,
        "messages": [AIMessage(content="Flight agent completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }

 
def hotel_agent(state: TravelState):
    query = f"Best hotels and areas to stay for: {state['user_query']}"

    raw_results = asyncio.run(tavily_search(query))

    print("\n========== HOTEL SEARCH RESULT ==========")
    print(raw_results)
    print("=========================================\n")

    prompt = f"""
You are an accommodation specialist. Below is a set of raw search results.
Provide highly concise hotel recommendations (max 200 words).
Extract exactly 3 hotels (1 budget, 1 mid-range, 1 luxury) with names, area, nightly price, and one pro/con.

User Request:
{state['user_query']}

Trip Constraints:
{state.get('trip_constraints', {})}

Raw Search Results:
{str(raw_results)[:3000]}

Format a clean recommendation report listing:
1. Recommended neighborhoods/areas
2. The 3 selected hotels
3. One direct booking tip
"""

    result = _llm_text(
        "You are a travel accommodation specialist.",
        prompt,
    )

    print("\n========== HOTEL AGENT OUTPUT ==========")
    print(result)
    print("=========================================\n")

    return {
        "hotel_results": result,
        "messages": [AIMessage(content="Hotel agent completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def weather_agent(state: TravelState):
    constraints = state["trip_constraints"]
    city = constraints["destination"]

    weather_data = asyncio.run(current_weather(city))
    forecast_data = asyncio.run(forecast(city))

    print("\n========== CURRENT WEATHER ==========")
    print(weather_data)
    print("=====================================\n")

    print("\n========== WEATHER FORECAST ==========")
    print(forecast_data)
    print("======================================\n")

    prompt = f"""
You are a travel weather specialist. Below is raw weather and forecast data for {city}.
Summarize this into a short, practical travel forecast (max 100 words).
Include:
1. Current temperature/conditions.
2. Brief 3-day overview.
3. Simple packing advice.

Raw Weather Data:
{str(weather_data)[:1000]}

Raw Forecast Data:
{str(forecast_data)[:2000]}
"""
    result = _llm_text(
        "You are a travel weather specialist.",
        prompt,
    )

    print("\n========== WEATHER AGENT OUTPUT ==========")
    print(result)
    print("==========================================\n")

    return {
        "weather_results": result,
        "messages": [AIMessage(content="Weather agent completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def budget_agent(state: TravelState):

    print("\n========== BUDGET AGENT INPUT ==========")
    print("Trip Constraints:")
    print(state.get("trip_constraints"))
    print("\nFlight Results:")
    print(state.get("flight_results"))
    print("\nHotel Results:")
    print(state.get("hotel_results"))
    print("\nWeather Results:")
    print(state.get("weather_results"))
    print("=========================================\n")

    prompt = f"""
Analyze whether this trip plan is realistic for the user's budget.
Provide a highly concise budget assessment (max 120 words).

User request:
{state['user_query']}

Constraints:
{state.get('trip_constraints', {})}

Flight results:
{state.get('flight_results', '')}

Hotel results:
{state.get('hotel_results', '')}

Weather results:
{state.get('weather_results', '')}

Include:
1. Estimated cost breakdown
2. Top 2 budget risks
3. Top 2 saving tips
4. Feasibility yes/no
"""

    result = _llm_text(
        "You are a practical travel budget analyst.",
        prompt,
    )

    print("\n========== BUDGET AGENT OUTPUT ==========")
    print(result)
    print("=========================================\n")

    return {
        "budget_results": result,
        "messages": [AIMessage(content="Budget agent completed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }

def itinerary_agent(state: TravelState):

    print("\n========== ITINERARY AGENT INPUT ==========")
    print("Trip Constraints:")
    print(state.get("trip_constraints"))

    print("\nFlight Results:")
    print(state.get("flight_results"))

    print("\nHotel Results:")
    print(state.get("hotel_results"))

    print("\nWeather Results:")
    print(state.get("weather_results"))

    print("\nBudget Results:")
    print(state.get("budget_results"))
    print("===========================================\n")

    prompt = f"""
Create a clear draft travel itinerary.

User request:
{state['user_query']}

Trip constraints:
{state.get('trip_constraints', {})}

Flight results:
{state.get('flight_results', '')}

Hotel results:
{state.get('hotel_results', '')}

Weather results:
{state.get('weather_results', '')}

Budget results:
{state.get('budget_results', '')}

Make the output structured, practical, and ready for human review.
"""

    result = _llm_text(
        "You are an expert itinerary planner.",
        prompt,
    )

    print("\n========== ITINERARY OUTPUT ==========")
    print(result)
    print("======================================\n")

    approval_request = f"""
Please review this draft travel plan.

{result}

Reply with approval or feedback.
"""

    return {
        "itinerary": result,
        "approval_request": approval_request,
        "messages": [AIMessage(content="Draft itinerary created for human review.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def human_approval_agent(state: TravelState):
    feedback = interrupt(
        {
            "question": "Do you approve this itinerary?",
            "draft_itinerary": state.get("itinerary", ""),
            "approval_request": state.get("approval_request", ""),
            "expected_response": {
                "approved": True,
                "feedback": "Optional feedback for revision",
            },
        }
    )

    approved = feedback["approved"]
    human_feedback = feedback["feedback"]

    return {
        "approved": approved,
        "human_feedback": human_feedback,
        "messages": [AIMessage(content="Human approval step completed.")],
    }



def final_response_agent(state: TravelState):
    print("\n========== FINAL AGENT INPUT ==========")
    print("Approved:", state.get("approved"))
    print("Feedback:", state.get("human_feedback"))
    print("=======================================\n")

    flight_info = state.get("flight_results", "")
    hotel_info = state.get("hotel_results", "")
    weather_info = state.get("weather_results", "")
    budget_info = state.get("budget_results", "")
    itinerary_info = state.get("itinerary", "")

    specialist_data = ""
    if flight_info:
        specialist_data += f"\nFlight Guidance:\n{flight_info}\n"
    if hotel_info:
        specialist_data += f"\nHotel Recommendations:\n{hotel_info}\n"
    if weather_info:
        specialist_data += f"\nWeather Outlook:\n{weather_info}\n"
    if budget_info:
        specialist_data += f"\nBudget Assessment:\n{budget_info}\n"

    if state["approved"]:
        prompt = f"""
The human approved the draft itinerary. 

Combine all the details into a cohesive, final polished travel plan.
Ensure the output integrates the flight guidance, hotel recommendations, weather outlook, budget assessment, and the day-by-day itinerary into a single, beautifully organized, user-ready document.

Draft itinerary:
{itinerary_info}

{specialist_data}
"""
    else:
        prompt = f"""
The human requested adjustments/revisions to the draft itinerary.

Original request:
{state['user_query']}

Human feedback / requested adjustments:
{state['human_feedback']}

Review the draft and feedback, and integrate the flight guidance, hotel recommendations, weather outlook, budget assessment, and updated day-by-day itinerary into a single, cohesive, final polished travel plan.

Draft itinerary:
{itinerary_info}

{specialist_data}
"""

    system_prompt = (
        "You are an expert travel concierge. You produce final user-ready travel plans.\n"
        "Do NOT output any thinking process, reasoning, planning steps, or mock tool calls.\n"
        "Return ONLY the final polished itinerary and travel plan in clean, beautiful, and highly readable markdown.\n"
        "Do not include any HTML tags, system logs, or JSON blocks. Make the presentation professional and clear for a normal traveler."
    )

    result = _llm_text(
        system_prompt,
        prompt,
    )

    print("\n========== FINAL RESPONSE ==========")
    print(result)

    return {
        "final_response": result,
        "messages": [AIMessage(content=result)],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
