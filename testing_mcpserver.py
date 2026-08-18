import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

load_dotenv()

# We use "or ''" to guarantee that AVIATION_STACK_API_KEY is a str, not str | None.
# Otherwise, the env dictionary would be inferred as dict[str, str | None],
# which is not assignable to dict[str, str] expected by StdioConnection.
AVIATION_STACK_API_KEY = os.getenv("AVIATION_STACK_API_KEY") or ""

client = MultiServerMCPClient(
    {
        "aviation_stack": {
            "transport": "stdio",
            "command": "/home/user/Documents/multi-agent travel planner/aviationstack-mcp/.venv/bin/python",
            "args": [
                "-m",
                "aviationstack_mcp",
                "mcp",
                "run"
            ],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY
            }
        }
    }
)

async def main():
    tools = await client.get_tools()

    print("available tools")
    for tool in tools:
        print(tool.name)

asyncio.run(main())
