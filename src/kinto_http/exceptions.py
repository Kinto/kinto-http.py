from typing import Any, List, Optional, Tuple


class KintoException(Exception):
    request: Any = None
    response: Any = None

    def __init__(self, message: Optional[str] = None, exception: Optional[Exception] = None):
        super().__init__(message)
        self.message: Optional[str] = message

        if exception is not None:
            self.request = getattr(exception, "request", None)
            self.response = getattr(exception, "response", None)
        else:
            self.request = None
            self.response = None

    def __str__(self) -> str:
        if self.request is not None and self.response is not None:
            return "{} {} - {} {}".format(
                self.request.method, self.request.path_url, self.response.status_code, self.message
            )
        return self.message or ""


class BucketNotFound(KintoException):
    pass


class CollectionNotFound(KintoException):
    pass


class BackoffException(KintoException):
    def __init__(
        self, message: Optional[str], backoff: int, exception: Optional[Exception] = None
    ):
        self.backoff = backoff
        super().__init__(message, exception)


class KintoBatchException(KintoException):
    def __init__(self, exceptions: List[Exception], results: List[Tuple[Any, Any]]):
        self.message = "\n".join([str(e) for e in exceptions])
        self.exceptions = exceptions
        self.results = results
