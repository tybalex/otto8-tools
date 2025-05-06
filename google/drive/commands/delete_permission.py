import os
from apis.permissions import delete_permission
from apis.helper import get_client


def delete_permission_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")
    permission_id = os.getenv("PERMISSION_ID")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return
    if not permission_id:
        print("Error: PERMISSION_ID environment variable is required but not set")
        return

    success = delete_permission(client, file_id, permission_id)
    if success:
        print(f"Successfully deleted permission: {permission_id}")
    else:
        print(f"Failed to delete permission: {permission_id}")
