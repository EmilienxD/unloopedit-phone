from lib.modules.paths import PathLike

from lib.config import Paths


class MaintenanceError(Exception):

    """
    An exception class for handling maintenance-related errors.

    Methods:
    -------
        __init__:
            Initializes the `MaintenanceError` instance with an error code and an additional message.
        parse_maintenance_documentation:
            Parses a maintenance documentation file and returns a dictionary of error information.
        _get_error_info:
            Retrieves error information based on the error code.
        _format_error_message:
            Formats the error message to include detailed information from the documentation.
    """

    def __init__(self, error_code: str, additional_message: str = ""):
        """
        Initializes the `MaintenanceError` instance with an error code and an additional message.

        Parameters:
        ----------
            error_code (str): The error code associated with the maintenance error.
            additional_message (str, optional): An optional additional message to include with the error. Defaults to an empty string.
            file_path (File, optional): The path to the maintenance documentation file. Defaults to DEFAULT_MAINTENANCE_PATH.
        """
        self.file_path = Paths('traceback/maintenance.txt')
        self.error_code = error_code
        self.additional_message = additional_message
        self.error_info = self._get_error_info()
        super().__init__(self._format_error_message())

    def parse_maintenance_documentation(self):
        """
        Parses a maintenance documentation file and returns a dictionary of error information.

        Parameters:
        ----------
            file_path (File, optional): The path to the maintenance documentation file. Defaults to DEFAULT_MAINTENANCE_PATH.

        Returns:
        -------
            dict: A dictionary containing error information grouped by category.
        """
        doc: str = self.file_path.read()

        maintenance_dict = {}
        groups = doc.strip().split('###')[1:]

        for group in groups:
            group = group.strip()
            group_lines = group.split('\n')
            group_name = group_lines[0]

            maintenance_dict[group_name] = {}

            errors = group.split('$')[1:]

            for error in errors:
                error = error.strip()
                if not error:
                    continue
                error_lines = error.split('\n')
                error_title = error_lines[0].strip()
                error_code = ""
                description = ""
                resolution = []
                is_resolution = False

                for line in error_lines[1:]:
                    line = line.strip()
                    if line.startswith('- Error Code:'):
                        error_code = line.split(':')[1].strip()
                    elif line.startswith('- Description:'):
                        description = line.split(':')[1].strip()
                    elif line.startswith('- Resolution:'):
                        is_resolution = True
                    elif is_resolution:
                        resolution.append(line)

                maintenance_dict[group_name][error_title] = {
                    "Error Code": error_code,
                    "Description": description,
                    "Resolution": ' '.join(resolution)
                }
                
        return maintenance_dict

    def _get_error_info(self) -> dict[str, any]:
        """
        Retrieves error information based on the error code.

        Returns:
        -------
            dict: A dictionary containing the error title, description, resolution, and group, or None if the error code is not found.
        """

        parsed_dict = self.parse_maintenance_documentation()
        for group, errors in parsed_dict.items():
            for error_title, error_details in errors.items():
                if error_details["Error Code"] == self.error_code:
                    return {
                        "title": error_title,
                        "description": error_details["Description"],
                        "resolution": error_details["Resolution"],
                        "group": group
                    }
                
        raise InvalidFileStructure(file_path=self.file_path)

    def _format_error_message(self):
        """
        Formats the error message to include detailed information from the documentation.

        Returns:
        -------
            str: The formatted error message.
        """
        if self.error_info:
            return (
                "\n___________________________________________________________________\n"
                f"- Error Code: {self.error_code}\n"
                f"- Group: {self.error_info['group']}\n"
                f"- Title: {self.error_info['title']}\n"
                f"- Description: {self.error_info['description']}\n"
                f"- Resolution: {self.error_info['resolution']}\n"
                f"- Additional Message: {self.additional_message}\n"
                "___________________________________________________________________\n"
            )
        else:
            return f"Error Code: {self.error_code}\nDescription: Error not found in the documentation.\nAdditional Message: {self.additional_message}"

class NoMoreValidAccountError(Exception):
    """
    Custom exception raised when no valid account is found.
    """

    def __init__(self, message: str = '', file_path: PathLike | None = None):
        """
        Initializes the NoMoreValidAccountError exception.

        Parameters:
        ----------
            file_path (str): The path to the accounts file.
            message (str, optional): Additional exception message. Defaults to None.
        """
        self.file_path = file_path
        self.message = message
        super().__init__(f"No valid account found{f' in {self.file_path}' if self.file_path else ''} | Script error: {self.message}")

class InvalidFileStructure(Exception):
    """
    An exception class for handling errors related to invalid file structures.

    Attributes:
    ----------
        file_path (str): The path to the file with the invalid structure.
        message (str): An optional message describing the error.

    Methods:
    -------
        __init__: Initializes the `InvalidFileStructure` instance with a file path and an optional message.
    """

    def __init__(self, file_path: PathLike | str, message: str = "The file %(file_path)% structure is invalid or the file is corrupted.", additional_message: str = ""):
        """
        Initializes the `InvalidFileStructure` instance with a file path and an optional message.

        Parameters:
        ----------
            file_path (str): The path to the file with the invalid structure.
            message (str, optional): An optional message describing the error. Defaults to a generic error message.
        """
        self.file_path = str(file_path)
        self.message = str(message)
        self.additional_message = str(additional_message)
        super().__init__(self.message.replace('%(file_path)%', self.file_path) + ' | ' + self.additional_message)

class WebResponseError(Exception):
    """
    An exception for all invalid web response, when a request don't work on the side of the website.
    """
    def __init__(self, message: str) -> None:
        super().__init__(message)

class PlanError(Exception):
    """
    An exception raised when tasks doesn't fit together.
    """
    def __init__(self, acc_name: str, task_name: str, plan_date: str, base_error: str | Exception=''):
        self.acc_name = acc_name
        self.task_name = task_name
        self.plan_date = plan_date
        self.base_error = base_error
        self.message = f'Error in plan task: {self.task_name} for account: {acc_name} at: {plan_date} | error origine: {self.base_error}'
        super().__init__(self.message)

class TaskDisabledError(Exception):
    """
    An exception raised when tasks doesn't fit together.
    """
    def __init__(self, task_name: str, base_error: str | Exception=''):
        self.task_name = task_name
        self.base_error = str(base_error)
        self.message = f'Implementaton error in task: {self.task_name} | error origine: {self.base_error} | enable this task or do it manually'
        super().__init__(self.message)

class ConfigError(Exception):
    """An exception raised when the config is invalid."""

class ObjectNotFoundError(Exception):
    def __init__(self, message: str | Exception=''):
        super().__init__(message)