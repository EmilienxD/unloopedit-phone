from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.paths import PathLike


### Common Errors ######################################################################################

class ObjectNotFoundError(Exception):
    pass


### Account Based Applications Erros ######################################################################################

class AccountNotFoundError(Exception):
    def __init__(self, *args, account: str = ''):
        super().__init__(f"Account{f' {account}' if account else ''} not found.", *args)

class NoMoreValidAccountError(Exception):
    """Custom exception raised when no valid account is found."""
    def __init__(self, *args, file_path: PathLike | None = None):
        super().__init__(f"No valid account found{f' in {file_path}' if file_path else ''}", *args)


### Web/http Errors ######################################################################################

class WebResponseError(Exception):
    """An exception for all invalid web response, when a request don't work on the side of the website."""
    pass



### API Erros ######################################################################################

class APIConnectionError(WebResponseError):
    def __init__(self, *args):
        super().__init__("Impossible to connect to the API.", *args)

class APIResponseError(WebResponseError):
    def __init__(self, *args):
        super().__init__("API retrieve an invalid response.", *args)

class APIQuotaLimitExceededError(WebResponseError):
    def __init__(self, *args):
        super().__init__("API quota limit exceeded.", *args)


### System/Workspace Maintenance Errors ######################################################################################

class InvalidFileSchemaError(Exception):
    """An exception class for handling errors related to invalid schema."""
    def __init__(self, *args, file_path: PathLike | None = None):
        super().__init__(f"The file{f' {file_path}' if file_path else ''} schema is invalid or the file is corrupted.", *args)

class ConfigError(Exception):
    """An exception raised when a config is invalid."""
    pass

class StorageLimitExceededError(Exception):
    """Raised when system folder storage capacity is exceeded."""
    def __init__(self, *args):
        super().__init__(
            "Error Code: System001\n"
            "Description: The folder has reached its storage limit.\n"
            "Resolution:\n"
            "1. Delete unneeded files or folders.\n"
            "2. Add an external drive or upgrade current storage.",
            *args
        )

class IncompleteWorkspaceError(Exception):
    """Raised when essential project files are missing or misplaced."""
    def __init__(self, *args):
        super().__init__(
            "Error Code: System002\n"
            "Description: An essential file is missing, causing an incomplete workspace.\n"
            "Resolution:\n"
            "1. Check for all essential files.\n"
            "2. Restore missing files from backup.\n"
            "3. Ensure all files are placed correctly.",
            *args
        )


### Development Errors ######################################################################################

class DevError(Exception):
    def __init__(self, *args):
        super().__init__("Illogical situation, might comes from a dev issue.", *args)


