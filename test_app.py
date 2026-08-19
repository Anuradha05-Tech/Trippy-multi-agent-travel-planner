import os
from dotenv import load_dotenv

dotenv_path = "/home/user/Documents/multi-agent travel planner/.env"
load_dotenv(dotenv_path=dotenv_path)

from langchain_core.messages import HumanMessage
from graph import app

print("Building graph and running app.invoke...")
try:
    result = app.invoke(
        {
            "messages": [HumanMessage(content="Plan a 3-day Paris trip under $1000. I prefer budget hotels.")],
            "user_id": "test_user",
            "user_query": "Plan a 3-day Paris trip under $1000. I prefer budget hotels.",
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "budget_results": "",
            "itinerary": "",
            "final_response": "",
            "llm_calls": 0,
        },
        config={"configurable": {"thread_id": "test_thread_123"}}
    )
    print("SUCCESS!")
    print("Supervisor plan:", result.get("supervisor_reasoning"))
    print("Selected agents:", result.get("selected_agents"))
    print("Interrupt?", "__interrupt__" in result)
except Exception as e:
    print("FAILED with error:")
    import traceback
    traceback.print_exc()
