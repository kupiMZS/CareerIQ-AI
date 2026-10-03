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


RETRYABLE_HTTP_STATUS_CODES = frozenset(
    {
        429,
        500,
        502,
        503,
        504,
    }
)


def is_retryable_provider_error(
    error: ProviderError,
) -> bool:
    if isinstance(
        error,
        (
            ProviderConnectionError,
            ProviderTimeoutError,
        ),
    ):
        return True

    if isinstance(
        error,
        ProviderHTTPError,
    ):
        return error.status_code in RETRYABLE_HTTP_STATUS_CODES

    return False
