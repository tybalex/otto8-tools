import os
from apis.files import update_file, get_file, FOLDER_MIME_TYPE
from apis.helper import get_client
from apis.workspace_file import load_from_gptscript_workspace


def update_file_tool() -> None:
    client = get_client("drive", "v3")
    file_id = os.getenv("FILE_ID")
    new_name = os.getenv("NEW_NAME")  # Optional
    new_parent_id = os.getenv("NEW_PARENT_ID")  # Optional
    new_workspace_file_path = os.getenv(
        "NEW_WORKSPACE_FILE_PATH"
    )  # Optional path to new content

    if not file_id:
        print("Error: FILE_ID parameter is required but not set")
        return

    mime_type = None
    new_content = None
    if new_workspace_file_path:
        try:
            new_content = load_from_gptscript_workspace(new_workspace_file_path)
        except Exception as e:
            print(
                f"Error: Failed to load file from GPTScript workspace: {e}\nContinuing with empty file content."
            )
            new_content = None

        if new_content:
            file_info = get_file(client, file_id, "mimeType")
            mime_type = file_info.get("mimeType")

            # Check if it's a folder
            if mime_type == FOLDER_MIME_TYPE:
                print(
                    "Warning: Cannot update content of a folder. Ignoring new content."
                )
                new_content = None
                mime_type = None

    file = update_file(
        client,
        file_id=file_id,
        new_name=new_name,
        new_content=new_content,
        mime_type=mime_type,
        new_parent_id=new_parent_id,
    )
    print(file)
