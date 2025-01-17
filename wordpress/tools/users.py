import requests
from tools.helper import WORDPRESS_API_URL, WORDPRESS_OAUTH_TOKEN, tool_registry


@tool_registry.register("GetMe")
def get_me():
    url = f"{WORDPRESS_API_URL}/me"
    headers = {
        "Authorization": f"Bearer {WORDPRESS_OAUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()


@tool_registry.register("ListMySites")
def list_my_sites():
    url = f"{WORDPRESS_API_URL}/me/sites"
    headers = {
        "Authorization": f"Bearer {WORDPRESS_OAUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()