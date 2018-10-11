class KintoException(Exception):
    request = None
    response = None

    def __init__(self, message=None, exception=None):
        super().__init__(message)
        self.message = message

        if exception is not None:
            self.request = exception.request
            self.response = exception.response
        else:
            self.request = None
            self.response = None

    def __str__(self):
        if self.request is not None and self.response is not None:
            return '{} {} - {} {}'.format(self.request.method, self.request.path_url,
                                          self.response.status_code, self.message)
        return self.message


class BucketNotFound(KintoException):
    pass


class BackoffException(KintoException):
    def __init__(self, message, backoff, exception=None):
        self.backoff = backoff
        super().__init__(message, exception)
