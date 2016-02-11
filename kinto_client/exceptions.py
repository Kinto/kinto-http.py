class KintoException(Exception):
    pass


class BucketNotFound(KintoException):
    request = None
    response = None

    def __init__(self, message=None, exception=None):
        super(BucketNotFound, self).__init__(self, message)
        self.message = message
        if exception is not None:
            self.request = exception.request
            self.response = exception.response
