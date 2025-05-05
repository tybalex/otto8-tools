import os
from apis.shared_drives import update_drive
from apis.helper import get_client


def update_drive_tool() -> None:
    client = get_client("drive", "v3")
    drive_id = os.getenv("DRIVE_ID")
    drive_name = os.getenv("DRIVE_NAME")

    if not drive_id:
        print("Error: DRIVE_ID environment variable is required but not set")
        return
    if not drive_name:
        print("Error: DRIVE_NAME environment variable is required but not set")
        return

    drive = update_drive(client, drive_id, drive_name)
    print(drive)
