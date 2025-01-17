from tools.helper import tool_registry, WORDPRESS_API_URL, WORDPRESS_OAUTH_TOKEN
import requests
import os


@tool_registry.register("GetSite")
def get_site():
    site_id_or_domain = os.environ["WORDPRESS_SITE_ID_OR_DOMAIN"]
    url = f"{WORDPRESS_API_URL}/sites/{site_id_or_domain}"
    headers = {
        "Authorization": f"Bearer {WORDPRESS_OAUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()