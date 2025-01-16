import requests
from tools.helper import WORDPRESS_API_URL, WORDPRESS_OAUTH_TOKEN

def get_users():
    url = f"{WORDPRESS_API_URL}/me"
    headers = {
        "Authorization": f"Bearer {WORDPRESS_OAUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_user_sites():
    url = f"{WORDPRESS_API_URL}/me/sites"
    headers = {
        "Authorization": f"Bearer {WORDPRESS_OAUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()