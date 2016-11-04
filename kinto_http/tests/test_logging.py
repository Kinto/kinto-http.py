import mock
from .support import unittest, mock_response
from kinto_http import Client


class BucketLoggingTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_create_bucket_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.create_bucket(
                bucket="buck",
                data={'foo': 'bar'})
            mocked_logger.info.assert_called_with(
                "Create bucket 'buck' with data {'foo': 'bar'}")

    def test_update_bucket_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.update_bucket(
                bucket="buck",
                data={'foo': 'bar'})
            mocked_logger.info.assert_called_with(
                "Update bucket 'buck' with data {'foo': 'bar'}")

    def test_get_bucket_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.get_bucket(
                bucket="buck")
            mocked_logger.info.assert_called_with(
                "Get bucket 'buck'")

    def test_delete_bucket_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.delete_bucket(
                bucket="buck")
            mocked_logger.info.assert_called_with(
                "Delete bucket 'buck'")

    def test_delete_buckets_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.delete_buckets()
            mocked_logger.info.assert_called_with(
                'Delete buckets for if_match None')


class GroupLoggingTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_create_group_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.create_group(
                'mozilla', bucket="buck",
                data={'foo': 'bar'},
                permissions={'write': ['blah', ]})
            mocked_logger.info.assert_called_with(
                "Create group 'mozilla' for bucket 'buck' with data {'foo': 'bar'} "
                "and permissions {'write': ['blah']}")

    def test_update_group_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.update_group(
                data={'foo': 'bar'},
                group='mozilla', bucket='buck',
                permissions={'write': ['blahblah', ]})
            mocked_logger.info.assert_called_with(
                "Update group 'mozilla' for bucket 'buck' with data {'foo': 'bar'} "
                "and permissions {'write': ['blahblah']}")

    def test_get_group_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.get_group(
                'mozilla', bucket='buck')
            mocked_logger.info.assert_called_with(
                "Get group 'mozilla' for bucket 'buck'")

    def test_delete_group_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.delete_group(
                'mozilla', bucket="buck")
            mocked_logger.info.assert_called_with(
                "Delete group 'mozilla' for bucket 'buck'")

    def test_delete_groups_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.delete_groups(
                bucket="buck")
            mocked_logger.info.assert_called_with(
                "Delete groups for bucket 'buck' for if_match None")


class CollectionLoggingTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_create_collection_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.create_collection(
                'mozilla', bucket="buck",
                data={'foo': 'bar'},
                permissions={'write': ['blah', ]})
            mocked_logger.info.assert_called_with(
                "Create collection 'mozilla' for bucket 'buck' with data {'foo': 'bar'} "
                "and permissions {'write': ['blah']}")

    def test_update_collection_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.update_collection(
                data={'foo': 'bar'},
                collection='mozilla', bucket='buck',
                permissions={'write': ['blahblah', ]})
            mocked_logger.info.assert_called_with(
                "Update collection 'mozilla' for bucket 'buck' with data {'foo': 'bar'} "
                "and permissions {'write': ['blahblah']}")

    def test_get_collection_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.get_collection(
                'mozilla', bucket='buck')
            mocked_logger.info.assert_called_with(
                "Get collection 'mozilla' for bucket 'buck'")

    def test_delete_collection_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.delete_collection(
                'mozilla', bucket="buck")
            mocked_logger.info.assert_called_with(
                "Delete collection 'mozilla' for bucket 'buck'")

    def test_delete_collections_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.delete_collections(
                bucket="buck")
            mocked_logger.info.assert_called_with(
                "Delete collections for bucket 'buck' for if_match None")


class RecordLoggingTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.MagicMock()
        self.client = Client(session=self.session)
        mock_response(self.session)

    def test_create_record_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.create_bucket('buck')
            self.client.create_collection('mozilla',
                                          bucket='buck')
            self.client.create_record(
                data={'foo': 'bar'},
                permissions={'write': ['blah', ]},
                bucket='buck',
                collection='mozilla')
            mocked_logger.info.assert_called_with(
                "Create record in collection 'mozilla' in bucket 'buck' with "
                "data {'foo': 'bar'} and permissions {'write': ['blah']}")

    def test_delete_records_logs_info_message(self):
        with mock.patch('kinto_http.logger') as mocked_logger:
            self.client.create_bucket('buck')
            self.client.create_collection('mozilla',
                                          bucket='buck')
            self.client.delete_records(
                bucket='buck',
                collection='mozilla')
            mocked_logger.info.assert_called_with(
                "Delete records from collection 'mozilla' in bucket 'buck'")
