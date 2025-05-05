import os
from apis.files import delete_file
from apis.helper import get_client


def delete_file_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return

    success = delete_file(client, file_id)
    if success:
        print(f"Successfully deleted file: {file_id}")
    else:
        print(f"Failed to delete file: {file_id}")
