import json
import logging
from collections import defaultdict

from kinto_http.exceptions import KintoException

from . import utils

logger = logging.getLogger(__name__)


class BatchSession(object):

    def __init__(self, client, batch_max_requests=0):
        self.session = client.session
        self.endpoints = client.endpoints
        self.batch_max_requests = batch_max_requests
        self.requests = []
        self._results = []

    def request(self, method, endpoint, data=None, permissions=None,
                headers=None):
        # Store all the requests in a dict, to be read later when .send()
        # is called.
        self.requests.append((method, endpoint, data, permissions, headers))
        # This is the signature of the session request.
        return defaultdict(dict), defaultdict(dict)

    def reset(self):
        # Reinitialize the batch request queue.
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
        self._results = []
        requests = self._build_requests()
        id_request = 0
        for chunk in utils.chunks(requests, self.batch_max_requests):
            kwargs = dict(method='POST',
                          endpoint=self.endpoints.get('batch'),
                          payload={'requests': chunk})
            resp, headers = self.session.request(**kwargs)
            for i, response in enumerate(resp['responses']):
                logger.debug("\nBatch #{}: \n\tRequest: {}\n\tResponse: {}\n".format(
                    id_request, json.dumps(chunk[i]), json.dumps(response)))
                status_code = response['status']
                if not (200 <= status_code < 400):
                    message = '{0} - {1}'.format(status_code, response['body'])
                    exception = KintoException(message)
                    exception.request = chunk[i]
                    exception.response = response
                if status_code > 499:
                    raise exception
                else:
                    if status_code < 400:
                        log = logger.warn
                        message = response["body"].get("message", "")
                    else:
                        log = logger.error
                        message = response["body"]["message"]
                    log("Batch #{}: {} {} - {} {}".format(
                        id_request, chunk[i]["method"], chunk[i]["path"],
                        status_code, message))
                id_request += 1

            self._results.append((resp, headers))

        return self._results

    def results(self):
        # Get each batch block response
        chunks = [resp for resp, _ in self._results]

        responses = []
        for chunk in chunks:
            responses += chunk['responses']

        return [resp['body'] for resp in responses]
