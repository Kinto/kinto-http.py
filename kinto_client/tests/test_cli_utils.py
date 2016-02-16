import argparse
import mock

from kinto_client import cli_utils
from .support import unittest

ALL_PARAMETERS = [
    ['-h', '--help'],
    ['-s', '--server'],
    ['-a', '--auth'],
    ['-b', '--bucket'],
    ['-c', '--collection'],
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

    def test_set_parser_server_options_create_a_parser_if_needed(self):
        parser = cli_utils.set_parser_server_options()
        self.assert_option_strings(parser, *ALL_PARAMETERS)
        assert len(parser._actions) == 8

    def test_set_parser_server_options_adds_arguments_on_existing_parser(self):
        parser = argparse.ArgumentParser(prog="importer")
        parser.add_argument('-t', '--type', help='File type',
                            type=str, default='xml')

        parser = cli_utils.set_parser_server_options(parser)
        self.assert_option_strings(parser, ['-t', '--type'],
                                   *ALL_PARAMETERS)
        assert len(parser._actions) == 9

    def test_can_change_default_values(self):
        parser = cli_utils.set_parser_server_options(
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
        parser = cli_utils.set_parser_server_options(
            default_server="https://firefox.settings.services.mozilla.com/",
            default_bucket="blocklists",
            default_collection="certificates")
        args = parser.parse_args(['-a', 'user:password'])
        assert args.auth == ('user', 'password')


class ClientFromArgsTest(unittest.TestCase):

    def setUp(self):
        parser = cli_utils.set_parser_server_options(
            default_server="https://firefox.settings.services.mozilla.com/",
            default_bucket="blocklists",
            default_collection="certificates",
            default_auth=('user', 'password')
        )

        self.args = parser.parse_args([])

    @mock.patch('kinto_client.cli_utils.Client')
    def test_create_client_from_args_build_a_client(self, mocked_client):
        cli_utils.create_client_from_args(self.args)
        mocked_client.assert_called_with(
            server_url='https://firefox.settings.services.mozilla.com/',
            auth=('user', 'password'),
            bucket='blocklists',
            collection='certificates')
