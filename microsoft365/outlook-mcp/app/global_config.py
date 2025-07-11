"""Global configuration constants and variables for the Outlook Mail tool."""

READ_ONLY_SCOPES = [
    "Mail.Read",
    "User.Read", 
    "MailboxSettings.Read",
    # "Groups.Read.All",
    "Files.Read.All"
]

ALL_SCOPES = [
    "Mail.Read",
    "Mail.ReadWrite", 
    "Mail.Send",
    "User.Read",
    "MailboxSettings.Read",
    # "Groups.ReadWrite.All",
    "Files.ReadWrite.All"
] 