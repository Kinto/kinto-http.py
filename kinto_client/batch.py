from . import utils
from collections import defaultdict

from kinto_client.exceptions import KintoException


class Batch(object):

    def __init__(self, client, batch_max_requests=0):
        self.session = client.session
        self.endpoints = client.endpoints
        self.batch_max_requests = batch_max_requests
        self.requests = []

    def request(self, method, endpoint, data=None, permissions=None,
                headers=None):
        # Store all the requests in a dict, to be read later when .send()
        # is called.
        self.requests.append((method, endpoint, data, permissions, headers))
        # This is the signature of the session request.
        return defaultdict(dict), defaultdict(dict)

    def reset(self):
        # Reinitialize the batch.
        self.requests = []

    def _build_requests(self):
        requests = []
        for (method, url, data, permissions, headers) in self.requests:
            # Strip the prefix in batch requests.
            request = {
                'method': method.upper(),
                'path': url.replace('v1/', '')}

            request['body'] = {}
            if data is not None:
                request['body']['data'] = data
            if permissions is not None:
                request['body']['permissions'] = permissions
            if headers is not None:
                request['headers'] = headers
            requests.append(request)
        return requests

    def send(self):
        result = []
        requests = self._build_requests()
        for chunk in utils.chunks(requests, self.batch_max_requests):
            resp, headers = self.session.request(
                'POST',
                self.endpoints.get('batch'),
                payload={'requests': chunk}
            )
            for i, response in enumerate(resp['responses']):
                status_code = response['status']
                if not (200 <= status_code < 400):
                    message = '{0} - {1}'.format(status_code, response['body'])
                    exception = KintoException(message)
                    exception.request = chunk[i]
                    exception.response = response
                    raise exception
            result.append((resp, headers))
        return result
