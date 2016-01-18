from kinto_client import Client
from kinto_client.exceptions import KintoException


def same_record(fields, one, two):
    for key in fields:
        if one.get(key) != two.get(key):
            return False
    return True


class Records(object):
    def __init__(self, options=None):
        if options is None:
            self.options = {}
        else:
            self.options = options
        self.records = self._load()

    def _load(self):
        raise NotImplementedError()

    def find(self, id):
        for rec in self.records:
            if rec['id'] == id:
                return rec


class KintoRecords(Records):
    def _load(self):
        self.client = Client(server_url=self.options['host'],
                             auth=self.options['auth'],
                             bucket=self.options['bucket'],
                             collection=self.options['collection'])

        # Create bucket
        try:
            self.client.create_bucket()
        except KintoException as e:
            if e.response.status_code != 412:
                raise e
        try:
            self.client.create_collection(
                permissions=self.options['permissions'])
        except KintoException as e:
            if e.response.status_code != 412:
                raise e

        return [self._kinto2rec(rec) for rec in
                self.client.get_records()]

    def _kinto2rec(self, record):
        return record

    def delete(self, data):
        self.client.delete_record(data['id'])

    def create(self, data):
        if 'id' not in data:
            data['id'] = create_id(data['key'])
        rec = self.client.create_record(data)
        return rec
