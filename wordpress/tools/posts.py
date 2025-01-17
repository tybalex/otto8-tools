import requests
import os
from tools.helper import WORDPRESS_API_URL, WORDPRESS_OAUTH_TOKEN, tool_registry


@tool_registry.register("ListPosts")
def list_posts():
    # TODO: this tool should support more parameters, such as number, search(search_query), status, etc.
    site_id_or_domain = os.environ["SITE_ID_OR_DOMAIN"]
    url = f"{WORDPRESS_API_URL}/sites/{site_id_or_domain}/posts/"
    headers = {
        "Authorization": f"Bearer {WORDPRESS_OAUTH_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return response.json()


@tool_registry.register("CreatePost")
def create_post():
    site_id_or_domain = os.environ["SITE_ID_OR_DOMAIN"]

    # Define the endpoint URL
    url = f'{WORDPRESS_API_URL}/sites/{site_id_or_domain}/posts/new'
    title = os.getenv("TITLE", "Untitled")
    content = os.getenv("CONTENT")
    status = os.getenv("STATUS", "publish")
    # Define the post data
    post_data = {
        'title': title,
        'content': content,
        'status': status,
    }

    # Define the headers with the authorization token
    headers = {
        'Authorization': f'Bearer {WORDPRESS_OAUTH_TOKEN}'
    }

    # Send the POST request to create the post
    response = requests.post(url, data=post_data, headers=headers)

    # Check the response
    if response.status_code == 200:
        print(f"Post created successfully! Post URL: {response.json()['URL']}")
    else:
        print(f"Error: {response.status_code}, {response.text}")