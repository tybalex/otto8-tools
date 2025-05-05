import os
from apis.files import create_file
from apis.helper import get_client
from apis.workspace_file import load_from_gptscript_workspace
import mimetypes


def create_file_tool() -> None:
    client = get_client("drive", "v3")
    file_name = os.getenv("FILE_NAME")
    if not file_name:
        print("Error: FILE_NAME environment variable is required but not set")
        return
    if "." not in file_name:
        print("Error: file_name parameter must contain a file extension")
        return
    mime_type = os.getenv("MIME_TYPE")
    parent_id = os.getenv("PARENT_ID")  # Optional
    workspace_file_path = os.getenv(
        "WORKSPACE_FILE_PATH"
    )  # Optional path to file content

    if not mime_type:
        # Try to infer MIME type from file extension
        guessed_type = mimetypes.guess_type(file_name)[0]
        if guessed_type:
            mime_type = guessed_type
        else:
            print(
                "Error: Could not determine MIME type from file extension. Please provide MIME_TYPE explicitly."
            )
            return

    try:
        file_content = load_from_gptscript_workspace(workspace_file_path)
    except Exception as e:
        print(
            f"Error: Failed to load file from GPTScript workspace: {e}\nContinuing with empty file content."
        )
        file_content = None

    file = create_file(
        client,
        name=file_name,
        mime_type=mime_type,
        parent_id=parent_id,
        file_content=file_content,
    )
    print(file)
