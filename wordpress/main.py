from tools.users import get_users, get_user_sites
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        sys.exit(1)

    command = sys.argv[1]
    match command:
        case "GetUsers":
            users = get_users()
            print(users)
        case "ListUserSites":
            sites = get_user_sites()
            print(sites)
        case _:
            print("Invalid command")
            sys.exit(1)

if __name__ == "__main__":
    main()
