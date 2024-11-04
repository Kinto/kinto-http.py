import argparse

from pytest_mock import MockerFixture

from kinto_http import BearerTokenAuth, cli_utils
from kinto_http.constants import ALL_PARAMETERS

from .support import assert_option_strings


def test_add_parser_options_create_a_parser_if_needed():
    parser = cli_utils.add_parser_options()
    assert_option_strings(parser, *ALL_PARAMETERS)
    assert len(parser._actions) == len(ALL_PARAMETERS)


def test_add_parser_options_adds_arguments_on_existing_parser():
    parser = argparse.ArgumentParser(prog="importer")
    parser.add_argument("-t", "--type", help="File type", type=str, default="xml")

    parser = cli_utils.add_parser_options(parser)
    assert_option_strings(parser, ["-t", "--type"], *ALL_PARAMETERS)
    assert len(parser._actions) == len(ALL_PARAMETERS) + 1


def test_add_parser_options_can_ignore_bucket_and_collection():
    parser = cli_utils.add_parser_options(include_bucket=False, include_collection=False)
    parameters = [
        ["-h", "--help"],
        ["-s", "--server"],
        ["-a", "--auth"],
        ["--retry"],
        ["--retry-after"],
        ["--ignore-batch-4xx"],
        ["-v", "--verbose"],
        ["-q", "--quiet"],
        ["-D", "--debug"],
    ]
    assert_option_strings(parser, *parameters)
    assert len(parser._actions) == len(parameters)


def test_can_change_default_values():
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/",
        default_bucket="blocklists",
        default_collection="certificates",
        default_auth="user:password",
    )

    args = vars(parser.parse_args([]))

    assert args == {
        "server": "https://firefox.settings.services.mozilla.com/",
        "auth": "user:password",
        "bucket": "blocklists",
        "collection": "certificates",
        "retry": 0,
        "retry_after": None,
        "verbosity": None,
        "ignore_batch_4xx": False,
    }


def test_get_auth_can_read_password_from_stdin(mocker: MockerFixture):
    mocked_getpass = mocker.patch("getpass.getpass")
    cli_utils.get_auth("admin")
    mocked_getpass.assert_called_with("Please enter a password for admin: ")


def test_get_auth_can_split_user_and_password():
    user, password = cli_utils.get_auth("user:password")
    assert user == "user"
    assert password == "password"


def test_get_auth_is_called_by_argparse():
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/",
        default_bucket="blocklists",
        default_collection="certificates",
    )
    args = parser.parse_args(["-a", "user:password"])
    assert args.auth == ("user", "password")


def test_create_client_from_default_args_build_a_client(mocker: MockerFixture):
    mocked_client = mocker.patch("kinto_http.cli_utils.Client")
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/",
        default_bucket="blocklists",
        default_collection="certificates",
        default_auth=("user", "password"),
    )

    args = parser.parse_args([])

    cli_utils.create_client_from_args(args)
    mocked_client.assert_called_with(
        server_url="https://firefox.settings.services.mozilla.com/",
        auth=("user", "password"),
        bucket="blocklists",
        collection="certificates",
        ignore_batch_4xx=False,
        retry=0,
        retry_after=None,
    )


def test_create_client_from_args_build_a_client(mocker: MockerFixture):
    mocked_client = mocker.patch("kinto_http.cli_utils.Client")
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/"
    )

    args = parser.parse_args(
        [
            "--auth",
            "user:password with spaces",
            "--bucket",
            "blocklists",
            "--collection",
            "certificates",
            "--retry",
            "3",
        ]
    )

    cli_utils.create_client_from_args(args)
    mocked_client.assert_called_with(
        server_url="https://firefox.settings.services.mozilla.com/",
        auth=("user", "password with spaces"),
        bucket="blocklists",
        collection="certificates",
        ignore_batch_4xx=False,
        retry=3,
        retry_after=None,
    )


def test_create_client_from_args_build_a_client_and_ask_for_password(mocker: MockerFixture):
    mocked_getpass = mocker.patch("getpass.getpass")
    mocked_client = mocker.patch("kinto_http.cli_utils.Client")
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/"
    )

    mocked_getpass.return_value = "password"

    args = parser.parse_args(
        [
            "--auth",
            "user",
            "--bucket",
            "blocklists",
            "--collection",
            "certificates",
            "--retry",
            "3",
        ]
    )

    cli_utils.create_client_from_args(args)
    mocked_getpass.assert_called_with("Please enter a password for user: ")
    mocked_client.assert_called_with(
        server_url="https://firefox.settings.services.mozilla.com/",
        auth=("user", "password"),
        bucket="blocklists",
        collection="certificates",
        ignore_batch_4xx=False,
        retry=3,
        retry_after=None,
    )


def test_create_client_from_args_default_bucket_and_collection_to_none(mocker: MockerFixture):
    mocked_client = mocker.patch("kinto_http.cli_utils.Client")
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/",
        default_auth=("user", "password"),
        include_bucket=False,
        include_collection=False,
    )

    args = parser.parse_args([])

    cli_utils.create_client_from_args(args)
    mocked_client.assert_called_with(
        server_url="https://firefox.settings.services.mozilla.com/",
        auth=("user", "password"),
        bucket=None,
        collection=None,
        ignore_batch_4xx=False,
        retry=0,
        retry_after=None,
    )


def test_create_client_from_args_with_bearer_token(mocker: MockerFixture):
    mocked_client = mocker.patch("kinto_http.cli_utils.Client")
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/"
    )

    args = parser.parse_args(["--auth", "Bearer Token_Containing:a:semicolon"])

    cli_utils.create_client_from_args(args)
    assert isinstance(mocked_client.call_args[1]["auth"], BearerTokenAuth)
    assert mocked_client.call_args[1]["auth"].type == "Bearer"
    assert mocked_client.call_args[1]["auth"].token == "Token_Containing:a:semicolon"


def test_create_client_from_args_with_basic_bearer_token(mocker: MockerFixture):
    mocked_client = mocker.patch("kinto_http.cli_utils.Client")
    parser = cli_utils.add_parser_options(
        default_server="https://firefox.settings.services.mozilla.com/"
    )

    args = parser.parse_args(["--auth", "Bearer Token.Dotted"])

    cli_utils.create_client_from_args(args)
    assert isinstance(mocked_client.call_args[1]["auth"], BearerTokenAuth)
    assert mocked_client.call_args[1]["auth"].type == "Bearer"
    assert mocked_client.call_args[1]["auth"].token == "Token.Dotted"
