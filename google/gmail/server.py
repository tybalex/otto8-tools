from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Literal, Union
import os
from apis.helpers import get_client, parse_label_ids, NON_PRIMARY_CATEGORIES_MAP, str_to_bool
from apis.messages import list_messages, message_to_string, modify_message_labels
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError
from apis.drafts import list_drafts
from apis.labels import list_labels, get_label, create_label, update_label, delete_label

# Configure server-specific settings
PORT = os.getenv("PORT", 9000)
MCP_PATH = os.getenv("MCP_PATH", "/mcp/gmail")

mcp = FastMCP(
    name="GmailMCPServer",
    on_duplicate_tools="error",                  # Handle duplicate registrations
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
)

@mcp.tool(
    exclude_args=["cred_token", "user_timezone"],
)
async def list_emails(
    max_results: Annotated[int, Field(description="Maximum number of emails to return.", ge=1, le=1000)] = 100,
    query: Annotated[str, Field(description="Query to search for emails.")] = "",
    label_ids: Annotated[str, Field(description="Comma-separated list of label IDs to filter emails by.")] = None,
    category: Annotated[Literal["primary", "social", "promotions", "updates", "forums"], Field(description="Category to filter emails by.")] = "primary",
    after: Annotated[str, Field(description="Date to search for emails after.")] = "",
    before: Annotated[str, Field(description="Date to search for emails before.")] = "",
    user_timezone: str = "UTC",
    cred_token: str = None) -> Union[list[str], str]:
    """
    List emails in the user's gmail account.
    If query is empty, list emails in the user's inbox.
    Otherwise, list emails matching the given query from all labels.
    """

    if "after:" in query or "before:" in query:
        raise ValueError(
            "Error: Please use the parameters `after` and `before` instead of having them in the `query`."
        )
    default_inbox = "INBOX"
    if query != "":
        default_inbox = ""  # if query is not empty, don't set inbox as default
    labels = label_ids or default_inbox
    label_ids = parse_label_ids(labels)

    main_query = query
    is_primary_category = False
    if any(
        label.upper() == "ALL" for label in label_ids
    ):  # check if ALL is in the label_ids
        label_ids = []
    elif "INBOX" in label_ids:
        if category in NON_PRIMARY_CATEGORIES_MAP:
            label_ids.append(
                NON_PRIMARY_CATEGORIES_MAP[category]
            )  # we use the internal category names for non-primary categories
        else:  # handle primary categories separately. use query to mimic gmail UI behavior
            main_query = f"{query} category:{category.lower()}"
            is_primary_category = True

    service = get_client(cred_token)
    response = list_messages(service, main_query, label_ids, max_results, after, before)
    if len(response) > 0:
        formatted_response = []
        for message in response:
            formatted_response.append(message_to_string(service, message, user_timezone)[1])
        return formatted_response

    # If not primary category or no results found, we can exit early
    if not is_primary_category:
        return "No emails found"

    # For primary category, ESTIMATE if the feature is enabled
    estimate_response = list_messages(
        service, "category:primary", ["INBOX"], 10, "", ""
    )
    if len(estimate_response) > 0:
        return "No emails found"

    # If categories aren't enabled, try without category filter
    no_category_response = list_messages(
        service, query, label_ids, max_results, after, before
    )
    if len(no_category_response) > 0:
        formatted_response = []
        for message in no_category_response:
            formatted_response.append(message_to_string(service, message, user_timezone)[1])
        return formatted_response

    return "No emails found"

@mcp.tool(
    exclude_args=["cred_token"],
)
async def list_drafts(
    max_results: Annotated[int, Field(description="Maximum number of drafts to return.", ge=1, le=1000)] = 100,
    cred_token: str = None
) -> list:
    """
    List drafts in the user's gmail account.
    """
    service = get_client(cred_token)
    drafts = await list_drafts(service, max_results)
    return drafts

@mcp.tool(
    exclude_args=["cred_token"],
)
def list_labels(
    label_id: Annotated[str, Field(description="Label ID to fetch (optional)")] = None,
    cred_token: str = None
) -> list[dict]:
    """
    Fetch a specific label by ID if provided, otherwise list all labels.
    """
    service = get_client(cred_token)
    if label_id:
        label = get_label(service, label_id)
        return [label]
    else:
        labels = list_labels(service)
        custom_labels = [l for l in labels if l.get("type") == "user"]
        return custom_labels

@mcp.tool(
    exclude_args=["cred_token"],
)
def create_label(
    label_name: Annotated[str, Field(description="Name of the label to create.")],
    label_list_visibility: Annotated[Literal["labelShow", "labelHide", "labelShowIfUnread"], Field(description="Label list visibility")] = "labelShow",
    message_list_visibility: Annotated[Literal["show", "hide"], Field(description="Message list visibility")] = "show",
    cred_token: str = None
) -> dict:
    """
    Create a new label in the user's gmail account.
    """
    service = get_client(cred_token)
    label = create_label(service, label_name, label_list_visibility, message_list_visibility)
    return label

@mcp.tool(
    exclude_args=["cred_token"],
)
def update_label(
    label_id: Annotated[str, Field(description="ID of the label to update.")],
    label_name: Annotated[str, Field(description="New name for the label")] = None,
    label_list_visibility: Annotated[Literal["labelShow", "labelHide", "labelShowIfUnread"], Field(description="Label list visibility")] = None,
    message_list_visibility: Annotated[Literal["show", "hide"], Field(description="Message list visibility")] = None,
    cred_token: str = None
) -> dict:
    """
    Update an existing label in the user's gmail account.
    """
    service = get_client(cred_token)
    label = update_label(service, label_id, label_name, label_list_visibility, message_list_visibility)
    return label

@mcp.tool(
    exclude_args=["cred_token"],
)
def delete_label(
    label_id: Annotated[str, Field(description="ID of the label to delete.")],
    cred_token: str = None
) -> str:
    """
    Delete a label in the user's gmail account.
    """
    service = get_client(cred_token)
    result = delete_label(service, label_id)
    return result

@mcp.tool(
    exclude_args=["cred_token"],
)
def modify_message_labels(
    email_id: Annotated[str, Field(description="ID of the email message to modify labels for.")],
    add_label_ids: Annotated[list[str], Field(description="List of label IDs to add")] = None,
    remove_label_ids: Annotated[list[str], Field(description="List of label IDs to remove")] = None,
    archive: Annotated[bool, Field(description="Whether to archive the message")] = None,
    mark_as_read: Annotated[bool, Field(description="Whether to mark the message as read")] = None,
    mark_as_starred: Annotated[bool, Field(description="Whether to mark the message as starred")] = None,
    mark_as_important: Annotated[bool, Field(description="Whether to mark the message as important")] = None,
    apply_action_to_thread: Annotated[bool, Field(description="Whether to apply action to the whole thread")] = False,
    cred_token: str = None
) -> dict:
    """
    Modify labels for a specific email.
    """
    service = get_client(cred_token)
    add_labels = parse_label_ids(add_label_ids) if add_label_ids else None
    remove_labels = parse_label_ids(remove_label_ids) if remove_label_ids else None
    res = modify_message_labels(
        service,
        email_id,
        add_labels,
        remove_labels,
        apply_action_to_thread,
        archive,
        mark_as_read,
        mark_as_starred,
        mark_as_important,
    )
    return res

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http", # fixed to streamable-http
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )