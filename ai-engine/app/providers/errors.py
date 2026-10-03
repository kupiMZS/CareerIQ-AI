class ProviderError(RuntimeError):
    """
    Base exception for expected AI provider failures.
    """


class ProviderConnectionError(ProviderError):
    """
    Raised when a provider cannot be reached.
    """


class ProviderTimeoutError(ProviderError):
    """
    Raised when a provider request times out.
    """


class ProviderHTTPError(ProviderError):
    """
    Raised when a provider returns an unsuccessful
    HTTP status code.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
    ):
        super().__init__(message)

        self.status_code = status_code


class ProviderResponseError(ProviderError):
    """
    Raised when a provider returns malformed or
    schema-invalid data.
    """
