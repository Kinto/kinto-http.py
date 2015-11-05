class KintoException(Exception):
    pass


class BucketNotFound(KintoException):
    def __init__(self, message, exception):
        super(BucketNotFound, self).__init__(self, message)
        self.message = message
        self.request = exception.request
        self.response = exception.response
