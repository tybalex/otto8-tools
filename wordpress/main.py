from tools import posts, users, sites # import to register tools
from tools.helper import tool_registry
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        sys.exit(1)

    command = sys.argv[1]
    try:
        json_response = tool_registry.get(command)()
        print(json.dumps(json_response, indent=4))
    except Exception as e:
        print(f"Running command: {' '.join(sys.argv)} yielded error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
