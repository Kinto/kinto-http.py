import argparse
import getpass
import logging

from . import Client


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
    return Client(server_url=args.server,
                  auth=args.auth,
                  bucket=getattr(args, 'bucket', None),
                  collection=getattr(args, 'collection', None))


class AuthAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if values is not None:
            setattr(namespace, self.dest, get_auth(values))


def add_parser_options(parser=None,
                       default_server=None,
                       default_auth=None,
                       default_bucket=None,
                       default_collection=None,
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

    if include_bucket:
        parser.add_argument('-b', '--bucket',
                            help='Bucket name.',
                            type=str, default=default_bucket)

    if include_collection:
        parser.add_argument('-c', '--collection',
                            help='Collection name.',
                            type=str, default=default_collection)

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
