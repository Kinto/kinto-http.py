from . import utils
from collections import defaultdict


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
            kwargs = dict(method='POST',
                          endpoint=self.endpoints.get('batch'),
                          payload={'requests': chunk})
            resp, headers = self.session.request(**kwargs)
            result.append((resp, headers))
        return result
