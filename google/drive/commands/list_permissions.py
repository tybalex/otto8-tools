import os
from apis.permissions import list_permissions
from apis.helper import get_client


def list_permissions_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return

    permissions = list_permissions(client, file_id)
    print(permissions)
