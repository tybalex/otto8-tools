import os
from apis.files import get_file
from apis.helper import get_client


def get_file_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")

    if not file_id:
        print("Error: FILE_ID environment variable is required but not set")
        return

    file = get_file(client, file_id)
    print(file)
