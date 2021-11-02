import argparse
import getpass
import logging

from . import BearerTokenAuth, Client


def get_auth(auth):
    """Ask for the user password if needed."""
    auth = tuple(auth.split(":", 1))
    if len(auth) < 2:
        user = auth[0]
        password = getpass.getpass("Please enter a password for %s: " % user)
        auth = (user, password)

    return auth


def create_client_from_args(args):
    """Return a client from parser args."""
    return Client(
        server_url=args.server,
        auth=args.auth,
        bucket=getattr(args, "bucket", None),
        collection=getattr(args, "collection", None),
        retry=args.retry,
        retry_after=args.retry_after,
        ignore_batch_4xx=args.ignore_batch_4xx,
    )


class AuthAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is not None:
            auth = None
            try:
                colonIndex = values.find(":")
                if colonIndex == -1 or values.index(" ") < colonIndex:
                    # Handle: `username:password with spaces` versus `Bearer TokenWith:Semicolon`
                    bearer_type, bearer_token = values.split(" ", 1)
                    auth = BearerTokenAuth(token=bearer_token, type=bearer_type)
            except ValueError:
                pass

            if auth is None:
                auth = get_auth(values)

            setattr(namespace, self.dest, auth)


def add_parser_options(
    parser=None,
    default_server=None,
    default_auth=None,
    default_retry=0,
    default_retry_after=None,
    default_ignore_batch_4xx=False,
    default_bucket=None,
    default_collection=None,
    include_bucket=True,
    include_collection=True,
    **kwargs
):

    if parser is None:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "-s",
        "--server",
        help="The location of the remote server (with prefix)",
        type=str,
        default=default_server,
    )

    parser.add_argument(
        "-a",
        "--auth",
        help="BasicAuth credentials: `token:my-secret` or " "Authorization header: `Bearer token`",
        type=str,
        default=default_auth,
        action=AuthAction,
    )

    if include_bucket:
        parser.add_argument(
            "-b", "--bucket", help="Bucket name.", type=str, default=default_bucket
        )

    if include_collection:
        parser.add_argument(
            "-c", "--collection", help="Collection name.", type=str, default=default_collection
        )

    parser.add_argument(
        "--retry", help="Number of retries when a request fails", type=int, default=default_retry
    )

    parser.add_argument(
        "--retry-after",
        help="Delay in seconds between retries when requests fail. "
        "(default: provided by server)",
        type=int,
        default=default_retry_after,
    )

    parser.add_argument(
        "--ignore-batch-4xx",
        help="Do not fail on 4xx errors in batch requests.",
        default=default_ignore_batch_4xx,
        action="store_true",
        dest="ignore_batch_4xx",
    )

    # Defaults
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=logging.INFO,
        dest="verbosity",
        help="Show all messages.",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.CRITICAL,
        dest="verbosity",
        help="Show only critical errors.",
    )

    parser.add_argument(
        "-D",
        "--debug",
        action="store_const",
        const=logging.DEBUG,
        dest="verbosity",
        help="Show all messages, including debug messages.",
    )

    return parser


def setup_logger(logger, args):  # pragma: nocover
    logger.addHandler(logging.StreamHandler())
    if args.verbosity:
        logger.setLevel(args.verbosity)
