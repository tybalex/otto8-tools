import os

WORDPRESS_API_URL = "https://public-api.wordpress.com/rest/v1.1"
WORDPRESS_OAUTH_TOKEN = os.environ["WORDPRESS_OAUTH_TOKEN"]


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

    def register(self, name):
        """
        A decorator that automatically registers the decorated function
        under the specified 'name' in the ToolRegistry.
        """

        def wrapper(func):
            self._register(name, func)
            return func

        return wrapper


tool_registry = ToolRegistry()