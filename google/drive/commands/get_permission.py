import os
from apis.permissions import get_permission
from apis.helper import get_client


def get_permission_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")
    permission_id = os.getenv("PERMISSION_ID")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return
    if not permission_id:
        print("Error: PERMISSION_ID environment variable is required but not set")
        return

    permission = get_permission(client, file_id, permission_id)
    print(permission)
