"""Microsoft Graph API interactions for Outlook Mail."""

import os
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import markdown
from msgraph import GraphServiceClient
from msgraph.generated.models.message import Message
from msgraph.generated.models.mail_folder import MailFolder
from msgraph.generated.models.group import Group
from msgraph.generated.models.conversation_thread import ConversationThread
from msgraph.generated.models.attachment import Attachment
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.file_attachment import FileAttachment
from msgraph.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder


@dataclass
class DraftInfo:
    """Information for creating a draft email."""
    subject: str
    body: str
    recipients: List[str]
    cc: List[str]
    bcc: List[str]
    attachments: List[str]
    reply_all: bool
    reply_to_email_id: str


async def list_messages(
    client: GraphServiceClient,
    folder_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    is_read: Optional[bool] = None
) -> List[Message]:
    """List messages from Outlook."""
    filters = []
    
    if start:
        filters.append(f"receivedDateTime ge {start}")
    if end:
        filters.append(f"receivedDateTime le {end}")
    if is_read is not None:
        filters.append(f"isRead eq {str(is_read).lower()}")
    
    if folder_id:
        # Get messages from specific folder
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            orderby=["receivedDateTime DESC"],
            top=limit if limit > 0 else None,
            filter=" and ".join(filters) if filters else None
        )
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        result = await client.me.mail_folders.by_mail_folder_id(folder_id).messages.get(
            request_configuration=request_config
        )
    else:
        # Get messages from all folders
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            orderby=["receivedDateTime DESC"],
            top=limit if limit > 0 else None,
            filter=" and ".join(filters) if filters else None
        )
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        result = await client.me.messages.get(request_configuration=request_config)
    
    return result.value if result and result.value else []


async def get_message_details(client: GraphServiceClient, message_id: str) -> Message:
    """Get details of a specific message."""
    result = await client.me.messages.by_message_id(message_id).get()
    return result


async def search_messages(
    client: GraphServiceClient,
    subject: Optional[str] = None,
    from_address: Optional[str] = None,
    from_name: Optional[str] = None,
    folder_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 10
) -> List[Message]:
    """Search for messages in Outlook."""
    filters = []
    
    # Add receivedDateTime filter (required for proper ordering)
    if end:
        filters.append(f"receivedDateTime le {end}")
    else:
        # Default to messages received before tomorrow
        tomorrow = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        filters.append(f"receivedDateTime le {tomorrow}")
    
    if subject:
        filters.append(f"contains(subject, '{subject}')")
    if from_address:
        filters.append(f"contains(from/emailAddress/address, '{from_address}')")
    if from_name:
        filters.append(f"contains(from/emailAddress/name, '{from_name}')")
    if start:
        filters.append(f"receivedDateTime ge {start}")
    
    if not filters:
        raise ValueError("At least one of subject, from_address, or from_name must be provided")
    
    if folder_id:
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            orderby=["receivedDateTime DESC"],
            filter=" and ".join(filters),
            top=limit
        )
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        result = await client.me.mail_folders.by_mail_folder_id(folder_id).messages.get(
            request_configuration=request_config
        )
    else:
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            orderby=["receivedDateTime DESC"],
            filter=" and ".join(filters),
            top=limit
        )
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        result = await client.me.messages.get(request_configuration=request_config)
    
    return result.value if result and result.value else []


def email_addresses_to_recipients(addresses: List[str]) -> List[Recipient]:
    """Convert email addresses to recipient objects."""
    recipients = []
    for address in addresses:
        if address.strip():
            email_addr = EmailAddress()
            email_addr.address = address.strip()
            recipient = Recipient()
            recipient.email_address = email_addr
            recipients.append(recipient)
    return recipients


async def create_draft(client: GraphServiceClient, info: DraftInfo) -> Message:
    """Create a draft email."""
    message = Message()
    message.is_draft = True
    message.subject = info.subject
    message.to_recipients = email_addresses_to_recipients(info.recipients)
    
    if info.cc:
        message.cc_recipients = email_addresses_to_recipients(info.cc)
    if info.bcc:
        message.bcc_recipients = email_addresses_to_recipients(info.bcc)
    
    # Convert markdown to HTML
    body = ItemBody()
    body.content_type = BodyType.Html
    body.content = markdown.markdown(info.body)
    message.body = body
    
    # Create the draft
    draft = await client.me.messages.post(message)
    
    # Attach files if any
    if info.attachments:
        await attach_files(client, draft.id, info.attachments)
    
    return draft


async def create_draft_reply(client: GraphServiceClient, info: DraftInfo) -> Message:
    """Create a draft reply to an existing email."""
    # Get the original message
    original_message = await client.me.messages.by_message_id(info.reply_to_email_id).get()
    
    # Create reply draft
    reply = Message()
    reply.is_draft = True
    
    # Set subject with "Re:" prefix if not already present
    subject = info.subject or original_message.subject or ""
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"
    reply.subject = subject
    
    # Set recipients
    if info.reply_all and original_message.reply_to:
        reply.to_recipients = original_message.reply_to
        if original_message.cc_recipients:
            reply.cc_recipients = original_message.cc_recipients
    else:
        reply.to_recipients = [original_message.sender] if original_message.sender else []
    
    # Override with provided recipients
    if info.recipients:
        reply.to_recipients = email_addresses_to_recipients(info.recipients)
    if info.cc:
        reply.cc_recipients = email_addresses_to_recipients(info.cc)
    if info.bcc:
        reply.bcc_recipients = email_addresses_to_recipients(info.bcc)
    
    # Set body
    body = ItemBody()
    body.content_type = BodyType.Html
    body.content = markdown.markdown(info.body)
    reply.body = body
    
    # Create the draft reply
    draft = await client.me.messages.by_message_id(info.reply_to_email_id).reply.post(reply)
    
    # Attach files if any
    if info.attachments:
        await attach_files(client, draft.id, info.attachments)
    
    return draft


async def attach_files(client: GraphServiceClient, draft_id: str, files: List[str]) -> None:
    """Attach files to a draft email."""
    for file_path in files:
        if not file_path:
            continue
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Attachment file not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        await upload_file(client, draft_id, file_path, file_data)


async def upload_file(client: GraphServiceClient, draft_id: str, file_path: str, data: bytes) -> None:
    """Upload a file as an attachment to a draft email."""
    filename = os.path.basename(file_path)
    
    attachment = FileAttachment()
    attachment.name = filename
    attachment.content_bytes = data
    attachment.content_type = "application/octet-stream"  # Default content type
    
    await client.me.messages.by_message_id(draft_id).attachments.post(attachment)


async def send_draft(client: GraphServiceClient, draft_id: str) -> None:
    """Send a draft email."""
    await client.me.messages.by_message_id(draft_id).send.post()


async def delete_message(client: GraphServiceClient, message_id: str) -> None:
    """Delete a message."""
    await client.me.messages.by_message_id(message_id).delete()


async def move_message(client: GraphServiceClient, message_id: str, destination_folder_id: str) -> Message:
    """Move a message to a different folder."""
    result = await client.me.messages.by_message_id(message_id).move.post({
        "destination_id": destination_folder_id
    })
    return result


async def get_me(client: GraphServiceClient):
    """Get current user information."""
    return await client.me.get()


async def list_attachments(client: GraphServiceClient, message_id: str) -> List[Attachment]:
    """List attachments for a message."""
    result = await client.me.messages.by_message_id(message_id).attachments.get()
    return result.value if result and result.value else []


async def get_attachment_content(client: GraphServiceClient, message_id: str, attachment_id: str) -> bytes:
    """Get attachment content."""
    attachment = await client.me.messages.by_message_id(message_id).attachments.by_attachment_id(attachment_id).get()
    if hasattr(attachment, 'content_bytes') and attachment.content_bytes:
        return attachment.content_bytes
    return b""


async def list_mail_folders(client: GraphServiceClient) -> List[MailFolder]:
    """List all mail folders."""
    result = await client.me.mail_folders.get()
    return result.value if result and result.value else []


async def list_groups(client: GraphServiceClient) -> List[Group]:
    """List all groups the user is a member of."""
    result = await client.me.joined_teams.get()
    return result.value if result and result.value else []


async def list_group_threads(
    client: GraphServiceClient,
    group_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100
) -> List[ConversationThread]:
    """List threads in a group."""
    query_params = {
        "top": limit if limit > 0 else None
    }
    
    filters = []
    if start:
        filters.append(f"lastDeliveredDateTime ge {start}")
    if end:
        filters.append(f"lastDeliveredDateTime le {end}")
    
    if filters:
        query_params["filter"] = " and ".join(filters)
    
    result = await client.groups.by_group_id(group_id).threads.get(
        request_configuration=query_params
    )
    return result.value if result and result.value else []


async def delete_group_thread(client: GraphServiceClient, group_id: str, thread_id: str) -> None:
    """Delete a group thread."""
    await client.groups.by_group_id(group_id).threads.by_conversation_thread_id(thread_id).delete()


async def download_onedrive_share_link(client: GraphServiceClient, share_link: str) -> bytes:
    """Download file from OneDrive share link."""
    # This is a simplified implementation
    # In practice, you'd need to decode the share link and use the appropriate API
    # For now, we'll raise an error indicating this needs implementation
    raise NotImplementedError("OneDrive share link download not yet implemented") 