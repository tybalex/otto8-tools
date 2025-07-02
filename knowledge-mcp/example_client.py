import asyncio
from fastmcp import Client
import os
import json
from fastmcp.client.transports import StreamableHttpTransport

PORT = os.getenv("PORT", "9000")
MCP_PATH = os.getenv("MCP_PATH", "/mcp/knowledge")

async def example_list_tools():
    async with Client(transport=StreamableHttpTransport(
        f"http://127.0.0.1:{PORT}{MCP_PATH}",
        headers={"x-forwarded-tenant-id": "123"},
    )) as client:
        await client.ping()
        
        # List available operations
        tools = await client.list_tools()
        for tool in tools:
            print(tool.name)

if __name__ == "__main__":
    asyncio.run(example_list_tools())
