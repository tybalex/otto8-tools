from apis.shared_drives import list_drives
from apis.helper import get_client


def list_drives_tool() -> None:
    client = get_client("drive", "v3")
    drives = list_drives(client)
    print(drives)
