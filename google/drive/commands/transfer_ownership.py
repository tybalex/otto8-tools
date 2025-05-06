import os
from apis.permissions import transfer_ownership
from apis.helper import get_client


def transfer_ownership_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")
    new_owner_email = os.getenv("NEW_OWNER_EMAIL")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return
    if not new_owner_email:
        print("Error: NEW_OWNER_EMAIL environment variable is required but not set")
        return

    permission = transfer_ownership(client, file_id, new_owner_email)
    print(permission)
