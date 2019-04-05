import argparse
import getpass
import logging

from . import Client, BearerTokenAuth


def get_auth(auth):
    """Ask for the user password if needed."""
    auth = tuple(auth.split(':', 1))
    if len(auth) < 2:
        user = auth[0]
        password = getpass.getpass('Please enter a password for %s: '
                                   % user)
        auth = (user, password)

    return auth


def create_client_from_args(args):
    """Return a client from parser args."""
    if args.bearer_token:
        auth = BearerTokenAuth(token=args.bearer_token, type=args.bearer_type)
    else:
        auth = args.auth
    return Client(server_url=args.server,
                  auth=auth,
                  bucket=getattr(args, 'bucket', None),
                  collection=getattr(args, 'collection', None),
                  retry=args.retry,
                  retry_after=args.retry_after,
                  ignore_batch_4xx=args.ignore_batch_4xx)


class AuthAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is not None:
            setattr(namespace, self.dest, get_auth(values))


def add_parser_options(parser=None,
                       default_server=None,
                       default_auth=None,
                       default_retry=0,
                       default_retry_after=None,
                       default_ignore_batch_4xx=False,
                       default_bucket=None,
                       default_collection=None,
                       default_bearer_token=None,
                       default_bearer_type="Bearer",
                       include_bucket=True,
                       include_collection=True,
                       **kwargs):

    if parser is None:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument('-s', '--server',
                        help='The location of the remote server (with prefix)',
                        type=str, default=default_server)

    parser.add_argument('-a', '--auth',
                        help='BasicAuth token:my-secret',
                        type=str, default=default_auth, action=AuthAction)

    parser.add_argument('--bearer-type',
                        help='Bearer token authorization realm. Default: Bearer',
                        type=str, default=default_bearer_type)

    parser.add_argument('--bearer-token',
                        help='Bearer Authorization token',
                        type=str, default=default_bearer_token)

    if include_bucket:
        parser.add_argument('-b', '--bucket',
                            help='Bucket name.',
                            type=str, default=default_bucket)

    if include_collection:
        parser.add_argument('-c', '--collection',
                            help='Collection name.',
                            type=str, default=default_collection)

    parser.add_argument('--retry',
                        help='Number of retries when a request fails',
                        type=int, default=default_retry)

    parser.add_argument('--retry-after',
                        help='Delay in seconds between retries when requests fail. '
                        '(default: provided by server)',
                        type=int, default=default_retry_after)

    parser.add_argument('--ignore-batch-4xx',
                        help='Do not fail on 4xx errors in batch requests.',
                        default=default_ignore_batch_4xx, action='store_true',
                        dest='ignore_batch_4xx')

    # Defaults
    parser.add_argument('-v', '--verbose', action='store_const',
                        const=logging.INFO, dest='verbosity',
                        help='Show all messages.')

    parser.add_argument('-q', '--quiet', action='store_const',
                        const=logging.CRITICAL, dest='verbosity',
                        help='Show only critical errors.')

    parser.add_argument('-D', '--debug', action='store_const',
                        const=logging.DEBUG, dest='verbosity',
                        help='Show all messages, including debug messages.')

    return parser


def setup_logger(logger, args):  # pragma: nocover
    logger.addHandler(logging.StreamHandler())
    if args.verbosity:
        logger.setLevel(args.verbosity)
