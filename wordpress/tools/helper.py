import requests
import os
from requests.auth import HTTPBasicAuth
from datetime import datetime

if "WORDPRESS_USERNAME" not in os.environ:
    raise ValueError("WORDPRESS_USERNAME is not set")

if "WORDPRESS_PASSWORD" not in os.environ:
    raise ValueError("WORDPRESS_PASSWORD is not set")

if "WORDPRESS_SITE" not in os.environ:
    raise ValueError("WORDPRESS_SITE is not set")

username = os.environ["WORDPRESS_USERNAME"]
password = os.environ["WORDPRESS_PASSWORD"]


WORDPRESS_BASIC_AUTH = HTTPBasicAuth(username, password)

WORDPRESS_SITE = os.environ["WORDPRESS_SITE"]
WORDPRESS_API_PATH = "/wp-json/wp/v2"


def clean_wordpress_site_url(site_url):

    if not site_url.startswith("https://") and not site_url.startswith("http://"):
        raise ValueError(
            f"Error: Invalid site URL: {site_url}. No scheme supplied, must start with protocol, e.g. https:// or http://"
        )

    site_url = site_url.rstrip("/")
    if site_url.endswith("/wp-json"):
        site_url = site_url.split("/wp-json")[0]

    site_url = site_url + WORDPRESS_API_PATH
    return site_url


WORDPRESS_API_URL = clean_wordpress_site_url(WORDPRESS_SITE)


def is_valid_iso8601(date_string):
    try:
        datetime.fromisoformat(date_string)
        return True
    except ValueError:
        return False


def str_to_bool(value):
    """Convert a string to a boolean."""
    return str(value).lower() in ("true", "1", "yes")


def create_session():
    session = requests.Session()
    session.auth = WORDPRESS_BASIC_AUTH
    headers = {
        "User-Agent": "curl",
    }
    session.headers.update(headers)
    return session


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
