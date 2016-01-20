import argparse
import logging
import mock
import os
import pytest

from kinto_client.importer import KintoImporter
from kinto_client.exceptions import KintoException

from .support import unittest

HERE = os.path.dirname(__file__)
logger = logging.getLogger()


class ImporterParserTest(unittest.TestCase):
    # Parser configuration
    def test_all_default_parameters_is_False_by_default(self):
        class DummyImporter(KintoImporter):
            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer")
        assert parser.format_help() == '''usage: importer [-h]

optional arguments:
  -h, --help  show this help message and exit
'''

    def test_can_change_all_default_parameters_at_the_class_level(self):
        class DummyImporter(KintoImporter):
            all_default_parameters = True

            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer")
        assert parser.format_help() == '''\
usage: importer [-h] [-s HOST] [-b BUCKET] [-c COLLECTION] [-u AUTH]
                [--verbose]
                N [N ...]

positional arguments:
  N                     A list of files to import.

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  Kinto Server
  -b BUCKET, --bucket BUCKET
                        Bucket name, usually the app name
  -c COLLECTION, --collection COLLECTION
                        Collection name
  -u AUTH, --auth AUTH  BasicAuth user:pass
  --verbose, -v         Display status
'''

    def test_can_change_all_default_parameters_at_the_method_level(self):
        class DummyImporter(KintoImporter):
            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer",
                                           all_default_parameters=True)
        assert parser.format_help() == '''\
usage: importer [-h] [-s HOST] [-b BUCKET] [-c COLLECTION] [-u AUTH]
                [--verbose]
                N [N ...]

positional arguments:
  N                     A list of files to import.

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  Kinto Server
  -b BUCKET, --bucket BUCKET
                        Bucket name, usually the app name
  -c COLLECTION, --collection COLLECTION
                        Collection name
  -u AUTH, --auth AUTH  BasicAuth user:pass
  --verbose, -v         Display status
'''

    def test_can_change_parser_arguments_at_the_class_level(self):
        class DummyImporter(KintoImporter):
            remote_server = True
            authentication = True
            files = True
            verbosity = True

            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer")
        assert parser.format_help() == '''\
usage: importer [-h] [-s HOST] [-b BUCKET] [-c COLLECTION] [-u AUTH]
                [--verbose]
                N [N ...]

positional arguments:
  N                     A list of files to import.

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  Kinto Server
  -b BUCKET, --bucket BUCKET
                        Bucket name, usually the app name
  -c COLLECTION, --collection COLLECTION
                        Collection name
  -u AUTH, --auth AUTH  BasicAuth user:pass
  --verbose, -v         Display status
'''

    def test_can_change_parser_arguments_at_the_method_level(self):
        class DummyImporter(KintoImporter):
            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer",
                                           remote_server=True,
                                           authentication=True,
                                           files=True,
                                           verbosity=True)
        assert parser.format_help() == '''\
usage: importer [-h] [-s HOST] [-b BUCKET] [-c COLLECTION] [-u AUTH]
                [--verbose]
                N [N ...]

positional arguments:
  N                     A list of files to import.

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  Kinto Server
  -b BUCKET, --bucket BUCKET
                        Bucket name, usually the app name
  -c COLLECTION, --collection COLLECTION
                        Collection name
  -u AUTH, --auth AUTH  BasicAuth user:pass
  --verbose, -v         Display status
'''

    def test_can_change_default_values(self):
        existing_file_path = os.path.join(HERE, 'samples', 'blocklists.xml')

        class DummyImporter(KintoImporter):
            remote_server = True
            authentication = True
            files = True
            verbosity = True

            default_host = "https://firefox.settings.services.mozilla.com/"
            default_bucket = "blocklists"
            default_collection = "certificates"
            default_auth = 'user:password'
            default_files = [existing_file_path, 'inexisting_file.xml']

            def __init__(self):
                self.logger = logger

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer")
        args = importer.get_arguments(parser, [])

        assert args == {
            'host': 'https://firefox.settings.services.mozilla.com/',
            'auth': ('user', 'password'),
            'bucket': 'blocklists',
            'collection': 'certificates',
            'files': [existing_file_path],
            'verbose': False,
        }

    def test_configure_parser_can_add_arguments_on_existing_parser(self):
        class DummyImporter(KintoImporter):
            all_default_parameters = True

            def __init__(self):
                self.logger = logger

        importer = DummyImporter()
        parser = argparse.ArgumentParser(prog="importer")
        parser.add_argument('-t', '--type', help='File type',
                            type=str, default='xml')

        parser = importer.configure_parser(parser)
        assert parser.format_help() == '''\
usage: importer [-h] [-t TYPE] [-s HOST] [-b BUCKET] [-c COLLECTION] [-u AUTH]
                [--verbose]
                N [N ...]

positional arguments:
  N                     A list of files to import.

optional arguments:
  -h, --help            show this help message and exit
  -t TYPE, --type TYPE  File type
  -s HOST, --host HOST  Kinto Server
  -b BUCKET, --bucket BUCKET
                        Bucket name, usually the app name
  -c COLLECTION, --collection COLLECTION
                        Collection name
  -u AUTH, --auth AUTH  BasicAuth user:pass
  --verbose, -v         Display status
'''

    # Parser value management
    def test_get_arguments_validate_if_given_files_exists(self):
        class DummyImporter(KintoImporter):
            def __init__(self):
                self.logger = logger

        importer = DummyImporter()
        parser = importer.configure_parser(files=True)
        args = importer.get_arguments(parser, ['inexistant_files.xml'])
        assert args['files'] == []

    def test_get_arguments_call_get_auth_method(self):
        class DummyImporter(KintoImporter):
            get_auth_called = False

            def __init__(self):
                self.logger = logger
            
            def get_auth(self, auth):
                self.get_auth_called = True
                return ('user', 'pass')

        importer = DummyImporter()
        parser = importer.configure_parser(authentication=True)
        importer.get_arguments(parser, ['-u', 'admin'])

        assert importer.get_auth_called is True

    @mock.patch('getpass.getpass')
    def test_get_auth_can_read_password_from_stdin(self, mocked_getpass):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            authentication = True

        DummyImporter(arguments=['-u', 'admin'])
        mocked_getpass.assert_called_with(
            'Please enter a password for admin: ')

    def test_verbosity_level_is_set_accordingly(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True

            def setup_remote_client(self):
                pass

        importer = DummyImporter(arguments=['-v'])
        assert importer.logger.level == logging.INFO

    def test_verbosity_level_is_set_to_command_log_level_by_default(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True

        importer = DummyImporter(arguments=[])
        assert importer.logger.level == logging.INFO


class ImporterTest(unittest.TestCase):
    def test_init_raise_an_error_if_record_fields_is_not_defined(self):
        with pytest.raises(ValueError) as excinfo:
            KintoImporter()

        assert 'record_fields attribute is not defined.' in str(excinfo.value)

    def test_default_get_local_records_raises_a_not_implemented_error(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)

        importer = DummyImporter(arguments=[])
        with pytest.raises(NotImplementedError):
            importer.local_records

    def test_setup_local_client_is_called_at_init(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True
            setup_local_client_called = False

            def setup_local_client(self):
                self.setup_local_client_called = True

        importer = DummyImporter(arguments=[])
        assert importer.setup_local_client_called

    def test_setup_remote_client_is_called_at_init(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True
            setup_remote_client_called = False

            def setup_remote_client(self):
                self.setup_remote_client_called = True

        importer = DummyImporter(arguments=[])
        assert importer.setup_remote_client_called

    def test_local_records_property_cache_records(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True
            get_local_records_call_count = 0

            def get_local_records(self):
                self.get_local_records_call_count += 1
                return [{"id": "abc", "info": "foobar"}]

        importer = DummyImporter(arguments=[])
        # Call a first time
        assert importer.local_records == {"abc": {"id": "abc",
                                                  "info": "foobar"}}
        assert importer.get_local_records_call_count == 1

        # Call a second time, should use the cache
        assert importer.local_records == {"abc": {"id": "abc",
                                                  "info": "foobar"}}
        assert importer.get_local_records_call_count == 1

    def test_remote_records_property_cache_records(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True
            get_remote_records_call_count = 0

            def get_remote_records(self):
                self.get_remote_records_call_count += 1
                return [{"id": "abc", "info": "foobar"}]

        importer = DummyImporter(arguments=[])
        # Call a first time
        assert importer.remote_records == {"abc": {"id": "abc",
                                                   "info": "foobar"}}
        assert importer.get_remote_records_call_count == 1

        # Call a second time, should use the cache
        assert importer.remote_records == {"abc": {"id": "abc",
                                                   "info": "foobar"}}
        assert importer.get_remote_records_call_count == 1

    def test_get_remote_records_call_remote_client_get_records(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)

            def setup_remote_client(self):
                self.remote_client = mock.MagicMock()
                self.args['host'] = 'localhost'

        importer = DummyImporter(arguments=[])
        importer.get_remote_records()

        importer.remote_client.get_records.assert_called_with()

    @mock.patch('kinto_client.importer.Client')
    def test_importer_configures_a_kinto_client(self, mocked_client):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            remote_server = True
            authentication = True
            default_auth = 'user:pass'

        importer = DummyImporter(arguments=['-b', 'blocklists',
                                            '-c', 'certificates'])
        mocked_client.assert_called_with(
            server_url='http://localhost:8888/v1',
            auth=('user', 'pass'),
            bucket='blocklists',
            collection='certificates')
        importer.remote_client.create_bucket.assert_called_with(
            permissions=None)
        importer.remote_client.create_collection.assert_called_with(
            permissions=None)

    @mock.patch('kinto_client.importer.Client')
    def test_importer_handles_existing_bucket(self, mocked_client):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            remote_server = True
            authentication = True
            default_auth = 'user:pass'

        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 412
        mocked_client().create_bucket.side_effect = exception

        DummyImporter(arguments=['-b', 'blocklists',
                                 '-c', 'certificates'])

    @mock.patch('kinto_client.importer.Client')
    def test_importer_handles_existing_collection(self, mocked_client):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            remote_server = True
            authentication = True
            default_auth = 'user:pass'

        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 412
        mocked_client().create_collection.side_effect = exception

        DummyImporter(arguments=['-b', 'blocklists',
                                 '-c', 'certificates'])

    @mock.patch('kinto_client.importer.Client')
    def test_importer_raise_on_bucket_creation_error(self, mocked_client):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            remote_server = True
            authentication = True
            default_auth = 'user:pass'

        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 403
        mocked_client().create_bucket.side_effect = exception

        with pytest.raises(KintoException):
            DummyImporter(arguments=['-b', 'blocklists',
                                     '-c', 'certificates'])

    @mock.patch('kinto_client.importer.Client')
    def test_importer_raise_on_collection_creation_error(self, mocked_client):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            remote_server = True
            authentication = True
            default_auth = 'user:pass'

        exception = KintoException()
        exception.response = mock.MagicMock()
        exception.response.status_code = 403
        mocked_client().create_collection.side_effect = exception

        with pytest.raises(KintoException):
            DummyImporter(arguments=['-b', 'blocklists',
                                     '-c', 'certificates'])


class ImporterSync(unittest.TestCase):
    def test_create_on_sync_can_be_deactivated_on_sync_at_method_level(self):
        pass

    def test_update_on_sync_can_be_deactivated_on_sync_at_method_level(self):
        pass

    def test_delete_on_sync_can_be_deactivated_on_sync_at_method_level(self):
        pass

    def test_create_on_sync_can_be_deactivated_on_sync_at_class_level(self):
        pass

    def test_update_on_sync_can_be_deactivated_on_sync_at_class_level(self):
        pass

    def test_delete_on_sync_can_be_deactivated_on_sync_at_class_level(self):
        pass
