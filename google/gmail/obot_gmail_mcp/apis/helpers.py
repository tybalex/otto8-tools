import logging
import os
import sys
from datetime import datetime, timezone
from typing import Union
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError
import pytz

NON_PRIMARY_CATEGORIES_MAP = {
    "social": "CATEGORY_SOCIAL",
    "promotions": "CATEGORY_PROMOTIONS",
    "updates": "CATEGORY_UPDATES",
    "forums": "CATEGORY_FORUMS",
}

GMAIL_BUILTIN_LABELS = {
    "INBOX",
    "SPAM",
    "TRASH",
    "DRAFT",
    "SENT",
    "IMPORTANT",
    "STARRED",
    "UNREAD",
    "CATEGORY_PERSONAL",
    "CATEGORY_SOCIAL",
    "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES",
    "CATEGORY_FORUMS",
}


def setup_logger(name):
    """Setup a logger that writes to sys.stderr. Avoid adding duplicate handlers.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        stderr_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "[Gmail Tool Debugging Log]: %(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)

    return logger


logger = setup_logger(__name__)


def parse_label_ids(label_ids_input: Union[str, list[str]]) -> list[str]:
    if isinstance(label_ids_input, str):
        if not label_ids_input.strip():
            return []
        label_ids_list = label_ids_input.split(",")
    else:
        label_ids_list = label_ids_input

    return [
        label.upper() if label.upper() in GMAIL_BUILTIN_LABELS else label
        for label in (l.strip() for l in label_ids_list)
        if label
    ]


def get_timezone(user_tz: str) -> ZoneInfo:

    try:
        tz = ZoneInfo(user_tz)
    except:
        tz = timezone.utc

    return tz


def get_client(cred_token: str, service_name: str = "gmail", version: str = "v1"):
    creds = Credentials(token=cred_token)
    try:
        service = build(serviceName=service_name, version=version, credentials=creds)
        return service
    except HttpError as err:
        raise HttpError(f"Error creating client, HTTP Error: {err}")


def extract_message_headers(message, user_tz: str):
    subject = None
    sender = None
    to = None
    cc = None
    bcc = None
    date = None

    if message is not None:
        label_ids = message.get("labelIds", [])
        for header in message["payload"]["headers"]:
            match header["name"].lower():
                case "subject":
                    subject = header["value"]
                case "from":
                    sender = header["value"]
                case "to":
                    to = header["value"]
                case "cc":
                    cc = header["value"]
                case "bcc":
                    bcc = header["value"]
        date = (
            datetime.fromtimestamp(int(message["internalDate"]) / 1000, timezone.utc)
            .astimezone(get_timezone(user_tz))
            .strftime("%Y-%m-%d %H:%M:%S %Z")
        )

    return subject, sender, to, cc, bcc, date, label_ids


async def prepend_base_path(base_path: str, file_path: str):
    """
    Prepend a base path to a file path if it's not already rooted in the base path.

    Args:
        base_path (str): The base path to prepend.
        file_path (str): The file path to check and modify.

    Returns:
        str: The modified file path with the base path prepended if necessary.

    Examples:
      >>> prepend_base_path("files", "my-file.txt")
      'files/my-file.txt'

      >>> prepend_base_path("files", "files/my-file.txt")
      'files/my-file.txt'

      >>> prepend_base_path("files", "foo/my-file.txt")
      'files/foo/my-file.txt'

      >>> prepend_base_path("files", "bar/files/my-file.txt")
      'files/bar/files/my-file.txt'

      >>> prepend_base_path("files", "files/bar/files/my-file.txt")
      'files/bar/files/my-file.txt'
    """
    # Split the file path into parts for checking
    file_parts = os.path.normpath(file_path).split(os.sep)

    # Check if the base path is already at the root
    if file_parts[0] == base_path:
        return file_path

    # Prepend the base path
    return os.path.join(base_path, file_path)


def format_query_timestamp(time_str: str):
    try:
        # Require full ISO 8601 with time and timezone offset
        # Example: 2024-04-16T00:00:00-07:00
        dt = datetime.fromisoformat(time_str)

        if dt.tzinfo is None:
            raise ValueError(
                "Datetime must include a timezone offset (e.g. -07:00 or Z)"
            )

        # Convert to UTC
        dt_utc = dt.astimezone(pytz.UTC)

        # Return UNIX timestamp (int, in seconds)
        return int(dt_utc.timestamp())

    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {e}")


def str_to_bool(value):
    """Convert a string to a boolean."""
    return str(value).lower() in ("true", "1", "yes")
