from tools.helper import tool_registry, ACCESS_TOKEN
from linkedin_api.clients.restli.client import RestliClient
from tools.users import get_user
import os
import json

@tool_registry.register_tool("CreatePost")
def create_post(client: RestliClient):
    r = get_user(client)
    user_id = r['sub']
    content = os.getenv("CONTENT")
    # if content is None or content == "":
    #     raise ValueError("Error: CONTENT is not set properly or empty.")
    
    share_media_category = os.getenv("SHARE_MEDIA_CATEGORY", "NONE")
    share_media_category_enum = ["NONE", "IMAGE", "ARTICLE"]
    if share_media_category not in share_media_category_enum:
        raise ValueError(f"Error: invalid SHARE_MEDIA_CATEGORY value: {share_media_category}. Must be one of {share_media_category_enum}")

    
    visibility = os.getenv("VISIBILITY", "PUBLIC")
    visibility_enum = ["PUBLIC", "CONNECTIONS"]
    if visibility not in visibility_enum:
        raise ValueError(f"Error: invalid VISIBILITY value: {visibility}. Must be one of {visibility_enum}")
    
    payload = {
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED", # it's always PUBLISHED
        "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": content
            },
                "shareMediaCategory": share_media_category,
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
    }
    
    if share_media_category != "NONE":
        title = os.getenv("SHARE_MEDIA_TITLE")
        description = os.getenv("SHARE_MEDIA_DESC")
        
        if share_media_category == "ARTICLE":
            if "SHARE_MEDIA_ORIGINAL_URL" not in os.environ:
                raise ValueError("Error: to create an article, SHARE_MEDIA_ORIGINAL_URL is required.")
            original_url = os.getenv("SHARE_MEDIA_ORIGINAL_URL")
            media_payload = [
                    {
                        "status": "READY",
                        "description": {
                            "text": description
                        },
                        "originalUrl": original_url,
                        "title": {
                            "text": title
                        }
                    }
                ]
        elif share_media_category == "IMAGE":
            upload_url, asset = register_upload(client)
            upload_file("test.png", upload_url)
            media_payload = [
                {
                    "status": "READY",
                    "description": {
                        "text": description
                    },
                    "media": asset,
                    "title": {
                        "text": title
                    }
                }
            ]
        
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_payload
        
        
    
    response = client.create(
        resource_path="/ugcPosts",
        entity=payload,
        access_token=ACCESS_TOKEN,
    )
    if response.status_code != 201:
        raise ValueError(f"Error: failed to create post. Status code: {response.status_code}. Response: {response.entity}")
    return response.entity


import requests

def register_upload(client: RestliClient):
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # File metadata could include information like file type, size, etc.
    user_id = get_user(client)['sub']
    data ={
    "registerUploadRequest": {
        "recipes": [
            "urn:li:digitalmediaRecipe:feedshare-image" # or live-video
        ],
        "owner": f"urn:li:person:{user_id}",
        "serviceRelationships": [
            {
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }
        ]
        }
    }
    
    # Send POST request
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        response_json = response.json()
        return response_json['value']["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"], response_json["value"]["asset"]
    else:
        return {"error": response.text}


def upload_file(file_path,  upload_url):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/octet-stream"
    }
    
    # Open the file in binary mode and read its content
    with open(file_path, 'rb') as file:
        # Upload the file using POST with file data
        data = file.read()  
        response = requests.post(upload_url, headers=headers, data=data)

    if response.status_code != 201:
        raise ValueError(f"Error: failed to upload file. Status code: {response.status_code}. Response: {response.text}")
    return response.status_code
