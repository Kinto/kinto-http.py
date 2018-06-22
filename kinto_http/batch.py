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
                payload=None, headers=None):
        # Store all the requests in a dict, to be read later when .send()
        # is called.
        payload = payload or {}
        if data is not None:
            payload['data'] = data
        if permissions is not None:
            payload['permissions'] = permissions

        self.requests.append((method, endpoint, payload, headers))
        # This is the signature of the session request.
        return defaultdict(dict), defaultdict(dict)

    def reset(self):
        # Reinitialize the batch request queue.
        self.requests = []

    def _build_requests(self):
        requests = []
        for (method, url, payload, headers) in self.requests:
            # Strip the prefix in batch requests.
            request = {
                'method': method.upper(),
                'path': url.replace('v1/', '')}

            request['body'] = payload
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
                status_code = response['status']
                if not (200 <= status_code < 400):
                    message = '{0} - {1}'.format(status_code, response['body'])
                    exception = KintoException(message)
                    exception.request = chunk[i]
                    exception.response = response

                level = logging.WARN if status_code < 400 else logging.ERROR
                message = response["body"].get("message", "")
                logger.log(level, "Batch #{}: {} {} - {} {}".format(
                    id_request, chunk[i]["method"], chunk[i]["path"],
                    status_code, message))

                # Full log in DEBUG mode
                logger.debug("\nBatch #{}: \n\tRequest: {}\n\tResponse: {}\n".format(
                    id_request, utils.json_dumps(chunk[i]), utils.json_dumps(response)))

                # Raise in case of a 500
                if status_code >= 500:
                    raise exception

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
