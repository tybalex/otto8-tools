from tools.helper import tool_registry, ACCESS_TOKEN
from linkedin_api.clients.restli.client import RestliClient


@tool_registry.register_tool("GetCurrentUser")
def get_user(client: RestliClient):
    response = client.get(resource_path="/userinfo", access_token=ACCESS_TOKEN)
    return response.entity
