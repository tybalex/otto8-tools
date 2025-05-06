import os
from apis.files import create_folder
from apis.helper import get_client


def create_folder_tool() -> None:
    """Create a new folder in Google Drive."""
    client = get_client("drive", "v3")
    folder_name = os.getenv("FOLDER_NAME")
    parent_id = os.getenv("PARENT_ID")  # Optional

    if not folder_name:
        print("Error: FOLDER_NAME environment variable is required but not set")
        return

    folder = create_folder(client, name=folder_name, parent_id=parent_id)
    print(folder)
