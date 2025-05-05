import os
from apis.shared_drives import delete_drive
from apis.helper import get_client


def delete_drive_tool() -> None:
    client = get_client("drive", "v3")
    drive_id = os.getenv("DRIVE_ID")

    if not drive_id:
        print("Error: DRIVE_ID environment variable is required but not set")
        return

    delete_drive(client, drive_id)
    print(f"Successfully deleted shared drive: {drive_id}")
