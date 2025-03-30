

class TimeLimitException(Exception):
    """
    Custom exception raised when a function exceeds its time limit.

    Attributes:
    ----------
        func_name (str): The name of the function.
        time_limit (float): The time limit in seconds.
        additionnal_message (str): Additional message for the exception.
    """

    def __init__(self, func_name: str, time_limit: float, additionnal_message: str=''):
        m, s = divmod(round(time_limit), 60)
        super().__init__(f'Func "{func_name}" exceeds time limit of {m} min {s} sec. | {additionnal_message}')