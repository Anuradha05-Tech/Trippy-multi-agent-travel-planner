import asyncio
import json
from typing import Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.types import interrupt
from config import get_llm

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

    content = response.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "".join(str(x) for x in content)
    return str(content)

from mcp_client import (
    current_weather, forecast, list_airlines, list_airports, tavily_search
)
from state import TravelState
