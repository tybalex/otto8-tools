import sys
from commands import (
    list_drives_tool,
    create_drive_tool,
    update_drive_tool,
    delete_drive_tool,
    list_files_tool,
    get_file_tool,
    create_file_tool,
    update_file_tool,
    delete_file_tool,
    transfer_ownership_tool,
    list_permissions_tool,
    get_permission_tool,
    create_permission_tool,
    update_permission_tool,
    delete_permission_tool,
    download_file_tool,
    copy_file_tool,
    create_folder_tool,
)
from apis.helper import setup_logger

logger = setup_logger(__name__)


def main():
    if len(sys.argv) < 2:
        print("Error: Command argument required")
        return

    command = sys.argv[1]

    commands = {
        "list_shared_drives": list_drives_tool,
        "create_shared_drive": create_drive_tool,
        "update_shared_drive": update_drive_tool,
        "delete_shared_drive": delete_drive_tool,
        "list_files": list_files_tool,
        "get_file": get_file_tool,
        "create_file": create_file_tool,
        "update_file": update_file_tool,
        "delete_file": delete_file_tool,
        "transfer_ownership": transfer_ownership_tool,
        "list_permissions": list_permissions_tool,
        "get_permission": get_permission_tool,
        "create_permission": create_permission_tool,
        "update_permission": update_permission_tool,
        "delete_permission": delete_permission_tool,
        "download_file": download_file_tool,
        "copy_file": copy_file_tool,
        "create_folder": create_folder_tool,
    }

    if command not in commands:
        print(f"Error: Unknown command '{command}'")
        return

    commands[command]()


if __name__ == "__main__":
    main()
