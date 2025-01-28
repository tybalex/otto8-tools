import os
import gptscript

ACCESS_TOKEN = os.getenv("LINKEDIN_OAUTH_TOKEN")
if ACCESS_TOKEN is None or ACCESS_TOKEN == "":
    raise Exception("Error: LINKEDIN_OAUTH_TOKEN is not set properly.")

def str_to_bool(value):
    """Convert a string to a boolean."""
    return str(value).lower() in ("true", "1", "yes")


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def _register(self, name, func):
        """
        Registers a tool by the given 'name'.
        Raises a ValueError if a tool with the same name is already registered.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = func

    def get(self, name):
        """
        Retrieves a registered tool by name.
        Raises a ValueError if the tool is not found.
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found.")
        return self._tools[name]

    def list_tools(self):
        """
        Returns a list of all registered tool names.
        """
        return list(self._tools.keys())

    def register_tool(self, name):
        """
        A decorator that automatically registers the decorated function
        under the specified 'name' in the ToolRegistry.
        """

        def wrapper(func):
            self._register(name, func)
            return func

        return wrapper


tool_registry = ToolRegistry()



def _prepend_base_path(base_path: str, file_path: str):
    """
    Prepend a base path to a file path if it's not already rooted in the base path.

    Args:
        base_path (str): The base path to prepend.
        file_path (str): The file path to check and modify.

    Returns:
        str: The modified file path with the base path prepended if necessary.

    Examples:
      >>> prepend_base_path("files", "my-file.txt")
      'files/my-file.txt'

      >>> prepend_base_path("files", "files/my-file.txt")
      'files/my-file.txt'

      >>> prepend_base_path("files", "foo/my-file.txt")
      'files/foo/my-file.txt'

      >>> prepend_base_path("files", "bar/files/my-file.txt")
      'files/bar/files/my-file.txt'

      >>> prepend_base_path("files", "files/bar/files/my-file.txt")
      'files/bar/files/my-file.txt'
    """
    # Split the file path into parts for checking
    file_parts = os.path.normpath(file_path).split(os.sep)

    # Check if the base path is already at the root
    if file_parts[0] == base_path:
        return file_path

    # Prepend the base path
    return os.path.join(base_path, file_path)


# for gptscript workspace S/L, see https://github.com/gptscript-ai/py-gptscript/blob/main/gptscript/gptscript.py
async def save_to_gptscript_workspace(filepath: str, content: bytes) -> None:
    gptscript_client = gptscript.GPTScript()
    wksp_file_path = _prepend_base_path("files", filepath)
    await gptscript_client.write_file_in_workspace(
        wksp_file_path, content
    )


async def load_from_gptscript_workspace(filepath: str) -> bytes:
    gptscript_client = gptscript.GPTScript()
    wksp_file_path = _prepend_base_path("files", filepath)
    file_content = await gptscript_client.read_file_in_workspace(wksp_file_path)
    return file_content
