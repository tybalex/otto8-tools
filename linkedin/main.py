from linkedin_api.clients.restli.client import RestliClient
from tools import (
    users,
    posts,
)  # pylint: disable=unused-import. These are used in the tool registry.
from tools.helper import tool_registry
import json
import sys
import asyncio


async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <tool_name>")
        sys.exit(1)

    command = sys.argv[1]
    client = RestliClient()

    response = await tool_registry.get(command)(client)
    print(json.dumps(response, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
