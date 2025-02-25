import sys
import json
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
API_ENDPOINT = 'https://discord.com/api/v10'

def main():

    if len(sys.argv) != 2:
        print(
            f"Error running command: {' '.join(sys.argv)} \nUsage: python3 main.py <command>"
        )
        sys.exit(1)

    command = sys.argv[1]
    try:
        
        if command == "GetMe":
            headers = {"Authorization": f"Bearer {TOKEN}"}
            response = requests.get("https://discord.com/api/users/@me", headers=headers)

            if response.status_code != 200:
                return f"Failed to fetch user: {response.text}", 400

            user = response.json()
            print(user)
        
        if command == "GetGuilds":
            headers = {"Authorization": f"Bearer {TOKEN}"}
            response = requests.get("https://discord.com/api/users/@me/guilds", headers=headers)

            if response.status_code != 200:
                return f"Failed to fetch servers: {response.text}", 400

            servers = response.json()
            print(servers)
        
        # json_response = tool_registry.get(command)()
        # print(json.dumps(json_response, indent=4))
    except Exception as e:
        print(f"Error running command: {' '.join(sys.argv)} \nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
