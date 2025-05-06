import os
from apis.shared_drives import create_drive
from apis.helper import get_client


def create_drive_tool() -> None:
    client = get_client("drive", "v3")
    drive_name = os.getenv("DRIVE_NAME")
    if not drive_name:
        print("Error: DRIVE_NAME environment variable is required but not set")
        return
    drive = create_drive(client, drive_name)
    print(drive)
