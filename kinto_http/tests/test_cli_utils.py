import argparse
import unittest
from unittest import mock

from kinto_http import cli_utils

ALL_PARAMETERS = [
    ['-h', '--help'],
    ['-s', '--server'],
    ['-a', '--auth'],
    ['-b', '--bucket'],
    ['-c', '--collection'],
    ['--retry'],
    ['--retry-after'],
    ['--ignore-4xx-errors'],
    ['-v', '--verbose'],
    ['-q', '--quiet'],
    ['-D', '--debug'],
]


class ParserServerOptionsTest(unittest.TestCase):
    def assert_option_strings(self, parser, *option_strings_list):
        for option_strings in option_strings_list:
            assert any([action.option_strings == option_strings
                        for action in parser._actions]), \
                "%s not found" % option_strings

    def test_add_parser_options_create_a_parser_if_needed(self):
        parser = cli_utils.add_parser_options()
        self.assert_option_strings(parser, *ALL_PARAMETERS)
        assert len(parser._actions) == 10

    def test_add_parser_options_adds_arguments_on_existing_parser(self):
        parser = argparse.ArgumentParser(prog="importer")
        parser.add_argument('-t', '--type', help='File type',
                            type=str, default='xml')

        parser = cli_utils.add_parser_options(parser)
        self.assert_option_strings(parser, ['-t', '--type'],
                                   *ALL_PARAMETERS)
        assert len(parser._actions) == 11

    def test_add_parser_options_can_ignore_bucket_and_collection(self):
        parser = cli_utils.add_parser_options(
            include_bucket=False, include_collection=False)
        parameters = [
            ['-h', '--help'],
            ['-s', '--server'],
            ['-a', '--auth'],
            ['--retry'],
            ['--retry-after'],
            ['-v', '--verbose'],
            ['-q', '--quiet'],
            ['-D', '--debug'],
        ]
        self.assert_option_strings(parser, *parameters)
        assert len(parser._actions) == 8

    def test_can_change_default_values(self):
        parser = cli_utils.add_parser_options(
            default_server="https://firefox.settings.services.mozilla.com/",
            default_bucket="blocklists",
            default_collection="certificates",
            default_auth='user:password'
        )

        args = vars(parser.parse_args([]))

        assert args == {
            'server': 'https://firefox.settings.services.mozilla.com/',
            'auth': 'user:password',
            'bucket': 'blocklists',
            'collection': 'certificates',
            'retry': 0,
            'retry_after': None,
            'verbosity': None
        }


class GetAuthTest(unittest.TestCase):
    @mock.patch('getpass.getpass')
    def test_get_auth_can_read_password_from_stdin(self, mocked_getpass):
        cli_utils.get_auth('admin')

        mocked_getpass.assert_called_with(
            'Please enter a password for admin: ')

    def test_get_auth_can_split_user_and_password(self):
        user, password = cli_utils.get_auth('user:password')
        assert user == "user"
        assert password == "password"

    def test_get_auth_is_called_by_argparse(self):
        parser = cli_utils.add_parser_options(
            default_server="https://firefox.settings.services.mozilla.com/",
            default_bucket="blocklists",
            default_collection="certificates")
        args = parser.parse_args(['-a', 'user:password'])
        assert args.auth == ('user', 'password')


class ClientFromArgsTest(unittest.TestCase):

    @mock.patch('kinto_http.cli_utils.Client')
    def test_create_client_from_default_args_build_a_client(self, mocked_client):
        parser = cli_utils.add_parser_options(
            default_server="https://firefox.settings.services.mozilla.com/",
            default_bucket="blocklists",
            default_collection="certificates",
            default_auth=('user', 'password')
        )

        args = parser.parse_args([])

        cli_utils.create_client_from_args(args)
        mocked_client.assert_called_with(
            server_url='https://firefox.settings.services.mozilla.com/',
            auth=('user', 'password'),
            bucket='blocklists',
            collection='certificates',
            ignore_4xx_errors=False,
            retry=0,
            retry_after=None)

    @mock.patch('kinto_http.cli_utils.Client')
    def test_create_client_from_args_build_a_client(self, mocked_client):
        parser = cli_utils.add_parser_options(
            default_server="https://firefox.settings.services.mozilla.com/",
        )

        args = parser.parse_args(['--auth', 'user:password',
                                  '--bucket', 'blocklists',
                                  '--collection', 'certificates',
                                  '--retry', '3'])

        cli_utils.create_client_from_args(args)
        mocked_client.assert_called_with(
            server_url='https://firefox.settings.services.mozilla.com/',
            auth=('user', 'password'),
            bucket='blocklists',
            collection='certificates',
            ignore_4xx_errors=False,
            retry=3,
            retry_after=None)

    @mock.patch('kinto_http.cli_utils.Client')
    def test_create_client_from_args_default_bucket_and_collection_to_none(
            self, mocked_client):
        parser = cli_utils.add_parser_options(
            default_server="https://firefox.settings.services.mozilla.com/",
            default_auth=('user', 'password'),
            include_bucket=False, include_collection=False
        )

        args = parser.parse_args([])

        cli_utils.create_client_from_args(args)
        mocked_client.assert_called_with(
            server_url='https://firefox.settings.services.mozilla.com/',
            auth=('user', 'password'),
            bucket=None,
            collection=None,
            ignore_4xx_errors=False,
            retry=0,
            retry_after=None)
