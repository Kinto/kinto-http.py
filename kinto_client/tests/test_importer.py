import argparse
import logging
import mock
import os
import pytest

import kinto_client
from kinto_client.exceptions import KintoException
from kinto_client.importer import KintoImporter

from .support import unittest

HERE = os.path.dirname(__file__)
logger = logging.getLogger()

ALL_PARAMETERS = [
    ['-h', '--help'],
    ['-s', '--host'],
    ['-u', '--auth'],
    ['-b', '--bucket'],
    ['-c', '--collection'],
    ['-v', '--verbose'],
]


class ImporterParserTest(unittest.TestCase):
    def assert_option_strings(self, parser, *option_strings_list):
        for option_strings in option_strings_list:
            assert any([action.option_strings == option_strings
                        for action in parser._actions]), \
                "%s not found" % option_strings

    def assert_files_nargs(self, parser, nargs='+'):
        for action in parser._actions:
            assert any([action.dest == 'files' and
                        action.nargs == nargs
                        for action in parser._actions])

    # Parser configuration
    def test_all_default_parameters_is_False_by_default(self):
        class DummyImporter(KintoImporter):
            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer")
        self.assert_option_strings(parser, ['-h', '--help'])
        assert len(parser._actions) == 1

    def test_can_change_all_default_parameters_at_the_class_level(self):
        class DummyImporter(KintoImporter):
            all_default_parameters = True

            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer")
        self.assert_option_strings(parser, *ALL_PARAMETERS)
        assert len(parser._actions) == 7

    def test_can_change_all_default_parameters_at_the_method_level(self):
        class DummyImporter(KintoImporter):
            def __init__(self):
                pass

        importer = DummyImporter()
        parser = importer.configure_parser(prog="importer",
                                           all_default_parameters=True)
        self.assert_option_strings(parser, *ALL_PARAMETERS)
        assert len(parser._actions) == 7

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
        self.assert_option_strings(parser, *ALL_PARAMETERS)
        assert len(parser._actions) == 7

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
        self.assert_option_strings(parser, *ALL_PARAMETERS)
        assert len(parser._actions) == 7

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
        self.assert_option_strings(parser, ['-t', '--type'],
                                   *ALL_PARAMETERS)
        assert len(parser._actions) == 8

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

            def setup_remote_client(self, remote_client=None):
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

            def setup_local_client(self, local_client=None):
                self.setup_local_client_called = True

        importer = DummyImporter(arguments=[])
        assert importer.setup_local_client_called

    def test_setup_remote_client_is_called_at_init(self):
        class DummyImporter(KintoImporter):
            record_fields = ('info',)
            verbosity = True
            setup_remote_client_called = False

            def setup_remote_client(self, remote_client=None):
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

            def setup_remote_client(self, remote_client=None):
                self.args['host'] = 'localhost'
                return mock.MagicMock()

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

        mocked_client.return_value = mock.MagicMock()
        DummyImporter(arguments=['-b', 'blocklists', '-c', 'certificates'])
        mocked_client.assert_called_with(
            server_url='http://localhost:8888/v1',
            auth=('user', 'pass'),
            bucket='blocklists',
            collection='certificates')

        mocked_client().create_bucket.assert_called_with(
            permissions=None)
        mocked_client().create_collection.assert_called_with(
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


class DummySyncImporter(KintoImporter):
    record_fields = ('name', 'protocol')

    def get_local_records(self):
        # Create websocket
        # Update HTTP to HTTPS
        # Delete Mail
        return [
            {'id': "f3a31016-274b-a558-6e21-d1a00f74090f",
             'name': "websocket",
             'protocol': "ws"},
            {'id': "2e6e434b-eac6-f84f-0905-e9f9bb7ab5ab",
             'name': "IRC",
             'protocol': "irc"},
            {'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
             'name': "HTTPS",
             'protocol': "https"}
        ]

    def get_remote_records(self):
        return [
            {'id': "2e6e434b-eac6-f84f-0905-e9f9bb7ab5ab",
             'name': "IRC",
             'protocol': "irc"},
            {'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
             'name': "HTTP",
             'protocol': "http"},
            {'id': "106b1b39-071f-dc61-e4e3-7e5b1063a5b2",
             'name': "Mail",
             'protocol': "mailto"}
        ]


class ImporterSyncTest(unittest.TestCase):
    def setUp(self):
        self.mocked_batch = mock.MagicMock()
        remote_client = kinto_client.Client(
            server_url="http://localhost:8888/v1",
            bucket='blocklists',
            collection='certificates')
        remote_client.batch = self.mocked_batch
        self.importer = DummySyncImporter(arguments=[],
                                          remote_client=remote_client)

    def test_create_on_sync_can_be_deactivated_on_sync_at_method_level(self):
        self.importer.sync(create=False)

        self.mocked_batch().__enter__().delete_record.assert_any_call(
            "106b1b39-071f-dc61-e4e3-7e5b1063a5b2")
        self.mocked_batch().__enter__().update_record.assert_any_call({
            'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
            'name': "HTTPS",
            'protocol': "https"
        })

    def test_update_on_sync_can_be_deactivated_on_sync_at_method_level(self):
        self.importer.sync(update=False)

        self.mocked_batch().__enter__().delete_record.assert_any_call(
            "106b1b39-071f-dc61-e4e3-7e5b1063a5b2")
        self.mocked_batch().__enter__().create_record.assert_any_call({
            'id': "f3a31016-274b-a558-6e21-d1a00f74090f",
            'name': "websocket",
            'protocol': "ws"
        })

    def test_delete_on_sync_can_be_deactivated_on_sync_at_method_level(self):
        self.importer.sync(delete=False)
        self.mocked_batch().__enter__().update_record.assert_any_call({
            'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
            'name': "HTTPS",
            'protocol': "https"
        })
        self.mocked_batch().__enter__().create_record.assert_any_call({
            'id': "f3a31016-274b-a558-6e21-d1a00f74090f",
            'name': "websocket",
            'protocol': "ws"
        })

    def test_create_on_sync_can_be_deactivated_on_sync_at_class_level(self):
        self.importer.create = False
        self.importer.sync()
        self.mocked_batch().__enter__().delete_record.assert_any_call(
            "106b1b39-071f-dc61-e4e3-7e5b1063a5b2")
        self.mocked_batch().__enter__().update_record.assert_any_call({
            'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
            'name': "HTTPS",
            'protocol': "https"
        })

    def test_update_on_sync_can_be_deactivated_on_sync_at_class_level(self):
        self.importer.update = False
        self.importer.sync()
        self.mocked_batch().__enter__().delete_record.assert_any_call(
            "106b1b39-071f-dc61-e4e3-7e5b1063a5b2")
        self.mocked_batch().__enter__().create_record.assert_any_call({
            'id': "f3a31016-274b-a558-6e21-d1a00f74090f",
            'name': "websocket",
            'protocol': "ws"
        })

    def test_delete_on_sync_can_be_deactivated_on_sync_at_class_level(self):
        self.importer.delete = False
        self.importer.sync()
        self.mocked_batch().__enter__().update_record.assert_any_call({
            'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
            'name': "HTTPS",
            'protocol': "https"
        })
        self.mocked_batch().__enter__().create_record.assert_any_call({
            'id': "f3a31016-274b-a558-6e21-d1a00f74090f",
            'name': "websocket",
            'protocol': "ws"
        })
