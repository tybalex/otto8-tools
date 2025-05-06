import os
from apis.permissions import update_permission
from apis.helper import get_client


def update_permission_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")
    permission_id = os.getenv("PERMISSION_ID")
    role = os.getenv("ROLE")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return
    if not permission_id:
        print("Error: PERMISSION_ID environment variable is required but not set")
        return
    if not role:
        print("Error: ROLE environment variable is required but not set")
        return

    permission = update_permission(client, file_id, permission_id, role)
    print(permission)
