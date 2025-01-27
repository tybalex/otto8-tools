from linkedin_api.clients.restli.client import RestliClient
from tools import users, posts
from tools.helper import tool_registry
import json
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <tool_name>")
        sys.exit(1)

    command = sys.argv[1]
    client = RestliClient()
    # from tools.posts import register_upload
    # upload_url, asset = register_upload(client)
    # print(upload_url, asset)
    
    response = tool_registry.get(command)(client)
    print(json.dumps(response, indent=4))


if __name__ == "__main__":
    main()
