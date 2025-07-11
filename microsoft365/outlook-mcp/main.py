import asyncio
from datetime import datetime
import os
import json
from typing import Optional, List, Dict, Any, Annotated

from fastmcp import FastMCP
from pydantic import Field
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from app.client import create_client
from app.global_config import READ_ONLY_SCOPES, ALL_SCOPES
from app.graph import (
    DraftInfo,
    list_messages,
    get_message_details,
    search_messages,
    create_draft as graph_create_draft,
    create_draft_reply,
    send_draft as graph_send_draft,
    delete_message,
    move_message,
    get_me,
    list_attachments as graph_list_attachments,
    get_attachment_content,
    list_mail_folders as graph_list_mail_folders,
    list_groups as graph_list_groups,
    list_group_threads as graph_list_group_threads,
    delete_group_thread as graph_delete_group_thread,
    download_onedrive_share_link as graph_download_onedrive_share_link
)
from app.utils import message_to_string, message_to_dict

mcp = FastMCP(
    name="OutlookMailMCP",
    on_duplicate_tools="error",
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
)


def _get_access_token():
    headers = get_http_headers()
    access_token = headers.get("x-forwarded-access-token", None)
    if not access_token:
        raise ToolError(
            "No access token found in headers, available headers: " + str(headers)
        )
    return access_token

def smart_split(s: str, sep: str) -> list[str]:
    """Split string by separator, return empty list if string is empty."""
    if not s:
        return []
    return s.split(sep)

@mcp.tool(name="list_mail_folders")
async def list_mail_folders() -> dict:
    """Lists all available Outlook mail folders."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        folders = await graph_list_mail_folders(client)
        
        # Return folders as a simple list
        folder_list = []
        for folder in folders:
            folder_list.append({
                "id": folder.id,
                "display_name": folder.display_name,
                "parent_folder_id": folder.parent_folder_id,
                "child_folder_count": folder.child_folder_count,
                "unread_item_count": folder.unread_item_count,
                "total_item_count": folder.total_item_count
            })
        
        return {"folders": folder_list}
    except Exception as e:
        raise ToolError(f"Failed to list mail folders: {e}")

@mcp.tool(name="list_emails")
async def list_emails(
    folder_id: Annotated[Optional[str], Field(description="The ID of the folder to list emails in. If unset, lists emails from all folders.")] = None,
    start: Annotated[Optional[str], Field(description="The RFC3339 formatted start date and time of the time frame to list emails within.")] = None,
    end: Annotated[Optional[str], Field(description="The RFC3339 formatted end date and time of the time frame to list emails within.")] = None,
    limit: Annotated[Optional[str], Field(description="The maximum number of emails to return. If unset, returns up to 100 emails.")] = None,
    read_status: Annotated[Optional[str], Field(description="The read status of the emails to list, valid values are 'read' or 'unread'. If unset, lists all emails.")] = None
) -> dict:
    """Lists emails in an Outlook folder."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
        # Parse parameters
        limit_int = 100  # default
        if limit:
            try:
                limit_int = int(limit)
                if limit_int < 1:
                    raise ValueError("limit must be a positive integer")
            except ValueError as e:
                raise ToolError(f"failed to parse limit: {e}")
        
        # Parse read status
        is_read = None
        if read_status:
            if read_status.lower() == "read":
                is_read = True
            elif read_status.lower() == "unread":
                is_read = False
            else:
                raise ToolError("read_status must be 'read', 'unread', or empty")
        
        # Get messages
        messages = await list_messages(
            client,
            folder_id=folder_id,
            start=start,
            end=end,
            limit=limit_int,
            is_read=is_read
        )
        
        # Convert messages to dictionaries for JSON serialization
        message_dicts = [message_to_dict(msg) for msg in messages]
        
        return {"messages": message_dicts}
    except Exception as e:
        raise ToolError(f"Failed to list emails: {e}")

@mcp.tool(name="get_email_details")
async def get_email_details(
    email_id: Annotated[str, Field(description="The ID of the email to get details for.")],
    group_id: Annotated[Optional[str], Field(description="If the email is in a group mailbox, the ID of the group mailbox is also required.")] = None,
    thread_id: Annotated[Optional[str], Field(description="If the email is in a group mailbox, the ID of the thread is also required.")] = None
) -> dict:
    """Get the details of an Outlook email."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
        if group_id and thread_id:
            # Handle group email details
            raise ToolError("Group email details not yet implemented")
        else:
            # Handle regular email details
            message = await get_message_details(client, email_id)
            message_str = await message_to_string(message, include_body=True)
            return {"email_details": message_str}
    except Exception as e:
        raise ToolError(f"Failed to get email details: {e}")

@mcp.tool(name="search_emails")
async def search_emails(
    subject: Annotated[Optional[str], Field(description="Search query for the subject of the email.")] = None,
    from_address: Annotated[Optional[str], Field(description="Search query for the email address of the sender.")] = None,
    from_name: Annotated[Optional[str], Field(description="Search query for the name of the sender.")] = None,
    folder_id: Annotated[Optional[str], Field(description="The ID of the folder to search in. If unset, will search all folders.")] = None,
    start: Annotated[Optional[str], Field(description="The start date and time of the time frame to search within, in RFC 3339 format.")] = None,
    end: Annotated[Optional[str], Field(description="The end date and time of the time frame to search within, in RFC 3339 format.")] = None,
    limit: Annotated[Optional[str], Field(description="The maximum number of emails to return. Default is 10.")] = None
) -> dict:
    """Search for emails in Outlook. At least one of subject, from_address, or from_name must be specified."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
        # Parse limit
        limit_int = 10  # default
        if limit:
            try:
                limit_int = int(limit)
            except ValueError as e:
                raise ToolError(f"failed to parse limit: {e}")
        
        # Search messages
        messages = await search_messages(
            client,
            subject=subject,
            from_address=from_address,
            from_name=from_name,
            folder_id=folder_id,
            start=start,
            end=end,
            limit=limit_int
        )
        
        # Convert messages to dictionaries for JSON serialization
        message_dicts = [message_to_dict(msg) for msg in messages]
        
        return {"messages": message_dicts}
    except Exception as e:
        raise ToolError(f"Failed to search emails: {e}")

@mcp.tool(name="create_draft")
async def create_draft(
    subject: Annotated[str, Field(description="The subject of the email.")],
    body: Annotated[str, Field(description="The body of the email in markdown format.")],
    recipients: Annotated[str, Field(description="A comma-separated list of email addresses to send the email to. No spaces. Example: person1@example.com,person2@example.com")],
    cc: Annotated[Optional[str], Field(description="A comma-separated list of email addresses to CC on the email. No spaces. Example: person1@example.com,person2@example.com")] = None,
    bcc: Annotated[Optional[str], Field(description="A comma-separated list of email addresses to BCC on the email. No spaces. Example: person1@example.com,person2@example.com")] = None,
    attachments: Annotated[Optional[str], Field(description="A comma separated list of workspace file paths to attach to the email.")] = None,
    reply_email_id: Annotated[Optional[str], Field(description="The ID of the email to reply to.")] = None,
    reply_all: Annotated[Optional[bool], Field(description="Whether to reply to all. If true, CC will be the original email's CC.")] = False
) -> dict:
    """Create (but do not send) a draft individual Outlook email."""
    try:
        client = create_client(ALL_SCOPES, _get_access_token())
        
        # Parse attachments
        attachment_list = []
        if attachments:
            attachment_list = smart_split(attachments, ",")
        
        info = DraftInfo(
            subject=subject,
            body=body,
            recipients=smart_split(recipients, ","),
            cc=smart_split(cc or "", ","),
            bcc=smart_split(bcc or "", ","),
            attachments=attachment_list,
            reply_all=reply_all,
            reply_to_email_id=reply_email_id or ""
        )
        
        if info.reply_to_email_id:
            draft = await create_draft_reply(client, info)
        else:
            draft = await graph_create_draft(client, info)
        
        return {"message": f"Draft created successfully. Draft ID: {draft.id}"}
    except Exception as e:
        raise ToolError(f"Failed to create draft: {e}")

# @mcp.tool(name="create_group_thread_email")
# async def create_group_thread_email(
#     group_id: Annotated[str, Field(description="The ID of the group to create the thread email in.")],
#     subject: Annotated[str, Field(description="The subject of the email.")],
#     body: Annotated[str, Field(description="The body of the email in markdown format.")],
#     reply_to_thread_id: Annotated[Optional[str], Field(description="The ID of the thread to reply to. If unset, a new thread will be created.")] = None,
#     recipients: Annotated[Optional[str], Field(description="The additional recipients to send the email to, must be a comma-separated list of email addresses.")] = None,
#     attachments: Annotated[Optional[str], Field(description="A comma separated list of workspace file paths to attach to the email.")] = None
# ) -> dict:
#     """Compose a group thread email in Outlook that is always sent to the Microsoft 365 group email address."""
#     try:
#         # This would need specific implementation for group thread emails
#         raise ToolError("Group thread email creation not yet implemented")
#     except Exception as e:
#         raise ToolError(f"Failed to create group thread email: {e}")

@mcp.tool(name="send_draft")
async def send_draft(
    draft_id: Annotated[str, Field(description="The ID of the draft to send.")]
) -> dict:
    """Send an existing draft email in Outlook."""
    try:
        client = create_client(ALL_SCOPES, _get_access_token())
        await graph_send_draft(client, draft_id)
        return {"message": f"Draft {draft_id} sent successfully"}
    except Exception as e:
        raise ToolError(f"Failed to send draft: {e}")

@mcp.tool(name="delete_email")
async def delete_email(
    email_id: Annotated[str, Field(description="The ID of the email to delete. This is NOT a mail folder ID.")]
) -> dict:
    """Delete an Outlook email."""
    try:
        client = create_client(ALL_SCOPES, _get_access_token())
        await delete_message(client, email_id)
        return {"message": f"Email {email_id} deleted successfully"}
    except Exception as e:
        raise ToolError(f"Failed to delete email: {e}")

@mcp.tool(name="move_email")
async def move_email(
    email_id: Annotated[str, Field(description="The ID of the email to move.")],
    destination_folder_id: Annotated[str, Field(description="The ID of the folder to move the email into.")]
) -> dict:
    """Moves an email to a different Outlook folder."""
    try:
        client = create_client(ALL_SCOPES, _get_access_token())
        result = await move_message(client, email_id, destination_folder_id)
        return {"message": f"Email {email_id} moved to folder {destination_folder_id}"}
    except Exception as e:
        raise ToolError(f"Failed to move email: {e}")

@mcp.tool(name="get_my_email_address")
async def get_my_email_address() -> dict:
    """Get the email address of the currently authenticated Outlook user."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        user = await get_me(client)
        return {"email": user.mail or user.user_principal_name}
    except Exception as e:
        raise ToolError(f"Failed to get email address: {e}")

@mcp.tool(name="list_attachments")
async def list_attachments(
    email_id: Annotated[str, Field(description="The ID of the email to list attachments for.")]
) -> dict:
    """List the attachments of an Outlook email."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        attachments = await graph_list_attachments(client, email_id)
        
        # Return attachments as a simple list
        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "name": attachment.name,
                "content_type": attachment.content_type,
                "size": attachment.size,
                "is_inline": attachment.is_inline
            })
        
        return {"attachments": attachment_list}
    except Exception as e:
        raise ToolError(f"Failed to list attachments: {e}")

@mcp.tool(name="download_attachment")
async def download_attachment(
    email_id: Annotated[str, Field(description="The ID of the email to get the attachment from.")],
    attachment_id: Annotated[str, Field(description="The ID of the attachment to get.")]
) -> dict:
    """Download an attachment from an Outlook email into workspace."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
        # Get attachment content
        content = await get_attachment_content(client, email_id, attachment_id)
        
        # Get attachment details for filename
        attachments = await graph_list_attachments(client, email_id)
        attachment_name = None
        for att in attachments:
            if att.id == attachment_id:
                attachment_name = att.name
                break
        
        if not attachment_name:
            attachment_name = f"attachment_{attachment_id}"
        
        # Save to workspace
        with open(attachment_name, 'wb') as f:
            f.write(content)
        
        return {"message": f"Downloaded attachment {attachment_name} to workspace"}
    except Exception as e:
        raise ToolError(f"Failed to download attachment: {e}")

@mcp.tool(name="read_attachment")
async def read_attachment(
    email_id: Annotated[str, Field(description="The ID of the email to get the attachment from.")],
    attachment_id: Annotated[str, Field(description="The ID of the attachment to get.")]
) -> dict:
    """Get the markdown converted contents of an attachment from an Outlook email."""
    try:
        client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
        # Get attachment content
        content = await get_attachment_content(client, email_id, attachment_id)
        
        # For now, just return the content as text
        # In a full implementation, you'd convert various file types to markdown
        try:
            text_content = content.decode('utf-8')
            return {"content": text_content}
        except UnicodeDecodeError:
            return {"error": "Binary attachment content cannot be displayed as text"}
    except Exception as e:
        raise ToolError(f"Failed to read attachment: {e}")

# @mcp.tool(name="list_groups")
# async def list_groups() -> dict:
#     """Lists all Microsoft 365 groups the user is a member of."""
#     try:
#         client = create_client(READ_ONLY_SCOPES, _get_access_token())
#         groups = await graph_list_groups(client)
        
#         # Return groups as a simple list
#         group_list = []
#         for group in groups:
#             group_list.append({
#                 "id": group.id,
#                 "display_name": group.display_name,
#                 "description": group.description,
#                 "mail": group.mail,
#                 "visibility": group.visibility
#             })
        
#         return {"groups": group_list}
#     except Exception as e:
#         raise ToolError(f"Failed to list groups: {e}")

# @mcp.tool(name="list_group_threads")
# async def list_group_threads(
#     group_id: Annotated[str, Field(description="The ID of the group to list threads in.")],
#     start: Annotated[Optional[str], Field(description="The RFC3339 formatted start date and time of the time frame to list threads within.")] = None,
#     end: Annotated[Optional[str], Field(description="The RFC3339 formatted end date and time of the time frame to list threads within.")] = None,
#     limit: Annotated[Optional[str], Field(description="The maximum number of threads to return. If unset, returns up to 100 threads.")] = None
# ) -> dict:
#     """Lists all group mailbox threads in a Microsoft 365 group. This will also return emails in the threads."""
#     try:
#         client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
#         # Parse limit
#         limit_int = 100  # default
#         if limit:
#             try:
#                 limit_int = int(limit)
#             except ValueError as e:
#                 raise ToolError(f"failed to parse limit: {e}")
        
#         threads = await graph_list_group_threads(
#             client,
#             group_id=group_id,
#             start=start,
#             end=end,
#             limit=limit_int
#         )
        
#         # Return threads as a simple list
#         thread_list = []
#         for thread in threads:
#             thread_list.append({
#                 "id": thread.id,
#                 "topic": thread.topic,
#                 "has_attachments": thread.has_attachments,
#                 "last_delivered_date_time": thread.last_delivered_date_time.isoformat() if thread.last_delivered_date_time else None,
#                 "unique_senders": thread.unique_senders
#             })
        
#         return {"threads": thread_list}
#     except Exception as e:
#         raise ToolError(f"Failed to list group threads: {e}")

# @mcp.tool(name="delete_group_thread")
# async def delete_group_thread(
#     group_id: Annotated[str, Field(description="The ID of the group to delete the thread from.")],
#     thread_id: Annotated[str, Field(description="The ID of the thread to delete.")]
# ) -> dict:
#     """Delete a group mailbox thread in Outlook."""
#     try:
#         client = create_client(ALL_SCOPES, _get_access_token())
#         await graph_delete_group_thread(client, group_id, thread_id)
#         return {"message": f"Group thread {thread_id} deleted successfully"}
#     except Exception as e:
#         raise ToolError(f"Failed to delete group thread: {e}")

# @mcp.tool(name="list_group_thread_email_attachments")
# async def list_group_thread_email_attachments(
#     group_id: Annotated[str, Field(description="The ID of the group containing the thread.")],
#     thread_id: Annotated[str, Field(description="The ID of the thread containing the email.")],
#     email_id: Annotated[str, Field(description="The ID of the email to list attachments for.")]
# ) -> dict:
#     """Lists all attachments in a specific Outlook group thread email."""
#     try:
#         # This would need specific implementation for group thread email attachments
#         raise ToolError("Group thread email attachments listing not yet implemented")
#     except Exception as e:
#         raise ToolError(f"Failed to list group thread email attachments: {e}")

# @mcp.tool(name="get_group_thread_email_attachment")
# async def get_group_thread_email_attachment(
#     group_id: Annotated[str, Field(description="The ID of the group containing the thread.")],
#     thread_id: Annotated[str, Field(description="The ID of the thread containing the email.")],
#     email_id: Annotated[str, Field(description="The ID of the email containing the attachment.")],
#     attachment_id: Annotated[str, Field(description="The ID of the attachment to get.")]
# ) -> dict:
#     """Get the markdown converted contents of an attachment from an Outlook group thread email."""
#     try:
#         # This would need specific implementation for group thread email attachments
#         raise ToolError("Group thread email attachment reading not yet implemented")
#     except Exception as e:
#         raise ToolError(f"Failed to get group thread email attachment: {e}")

# @mcp.tool(name="download_group_thread_email_attachment")
# async def download_group_thread_email_attachment(
#     group_id: Annotated[str, Field(description="The ID of the group containing the thread.")],
#     thread_id: Annotated[str, Field(description="The ID of the thread containing the email.")],
#     email_id: Annotated[str, Field(description="The ID of the email containing the attachment.")],
#     attachment_id: Annotated[str, Field(description="The ID of the attachment to download.")]
# ) -> dict:
#     """Download an attachment from an Outlook group thread email into the workspace."""
#     try:
#         # This would need specific implementation for group thread email attachments
#         raise ToolError("Group thread email attachment download not yet implemented")
#     except Exception as e:
#         raise ToolError(f"Failed to download group thread email attachment: {e}")

# @mcp.tool(name="download_onedrive_share_link")
# async def download_onedrive_share_link(
#     share_link: Annotated[str, Field(description="The OneDrive share link")]
# ) -> dict:
#     """Download the file from a OneDrive share link to the workspace."""
#     try:
#         client = create_client(READ_ONLY_SCOPES, _get_access_token())
        
#         content = await graph_download_onedrive_share_link(client, share_link)
        
#         # Extract filename from share link or use default
#         filename = "onedrive_download"
        
#         with open(filename, 'wb') as f:
#             f.write(content)
        
#         return {"message": f"Downloaded OneDrive file to {filename}"}
#     except NotImplementedError as e:
#         raise ToolError(f"Error: {e}")
#     except Exception as e:
#         raise ToolError(f"Failed to download OneDrive share link: {e}")

def streamable_http_server():
    """Main entry point for the Gmail MCP server."""
    mcp.run(
        transport="streamable-http",  # fixed to streamable-http
        host="0.0.0.0",
        port=9000,
        path="/mcp/outlook",
    )

if __name__ == "__main__":
    streamable_http_server()