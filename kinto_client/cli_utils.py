import getpass

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


def client_from_args(args):
    """Return a client from parser args."""
    return Client(server_url=args.server,
                  auth=get_auth(args.auth),
                  bucket=args.bucket,
                  collection=args.collection)


def add_importer_server_options(parser,
                                default_server=None,
                                default_auth=None,
                                default_bucket=None,
                                default_collection=None):

    parser.add_argument('-s', '--server', help='Kinto Server',
                        type=str, default=default_server)

    parser.add_argument('-a', '--auth',
                        help='BasicAuth token:my-secret',
                        type=str, default=default_auth)

    parser.add_argument('-b', '--bucket',
                        help='Bucket name, usually the app name',
                        type=str, default=default_bucket)

    parser.add_argument('-c', '--collection',
                        help='Collection name',
                        type=str, default=default_collection)
