import os
import asyncio
from typing import Any

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        }
    }
)

# Initialize the global variable to avoid NameError/linter issues
search_tool: Any = None


async def main():
    tools = await client.get_tools()
   
    search_tool_local = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )

    result = await search_tool_local.ainvoke({
        "query": "search for hotels in new york city"
    })

    print(result)


async def initialize_mcp():
    global search_tool
    if search_tool is not None:
        return

    tools = await client.get_tools()
    print("Available MCP tools: ")

    for tool in tools:
        print(tool.name)
   
    search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )
    

async def tavily_mcp_search(query: str):
    global search_tool
    await initialize_mcp()
    if search_tool is None:
        raise RuntimeError("MCP search tool could not be initialized.")
    result = await search_tool.ainvoke({
        "query": query
    })
    return result