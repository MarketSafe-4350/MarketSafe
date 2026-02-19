class ApiError(Exception):
    """Custom exception class for API errors.

    Args:
        Exception (_type_): Base exception class.
    """

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        if value is None:
            raise ValueError("status code cannot be None")
        self._status_code = value

    @property
    def message(self):
        return self._status_code

    @message.setter
    def message(self, value):
        if value is None:
            return ValueError("message cannot be None")
        self._message = value
