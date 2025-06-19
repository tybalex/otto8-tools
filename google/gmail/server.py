from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Literal, Union
import os
from apis.helpers import get_client, parse_label_ids, NON_PRIMARY_CATEGORIES_MAP
from apis.messages import list_messages, message_to_string
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError

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


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http", # fixed to streamable-http
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )