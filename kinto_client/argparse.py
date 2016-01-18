from __future__ import absolute_import
import logging

COMMAND = 25
logging.addLevelName(COMMAND, 'COMMAND')
logging.basicConfig(level=COMMAND, format="%(message)s")


def get_parser(*args, **kwargs):
    """Return an argparse.ArgumentParser pre-configured object."""

    parser = argparse.ArgumentParser(*args, **kwargs)

    parser.add_argument('-s', '--host', help='Kinto Server',
                        type=str, default=DEFAULT_KINTO_SERVER)

    parser.add_argument('-u', '--auth', help='BasicAuth user:pass',
                        type=str, default=DEFAULT_USER_NAME)

    parser.add_argument('-b', '--bucket',
                        help='Bucket name, usually the app name',
                        type=str)

    parser.add_argument('-c', '--collection',
                        help='Collection name, usually the locale code',
                        type=str)

    parser.add_argument('files', metavar='N', type=str, nargs='+',
                        help='A list of properties file for the locale.')

    parser.add_argument('--verbose', '-v',
                        help='Display status',
                        dest='verbose',
                        action='store_true')

    return parser


def setup_parser(parser, logger):
    """Parse arguments and configure the logger."""
    args = vars(parser.parse_args(args=args))
    verbose = args['verbose']

    if verbose:
        logger.setLevel(logging.INFO)

    files = []
    for f in args['files']:
        if os.path.exists(f):
            files.append(os.path.abspath(f))
            logger.log(COMMAND, '%s: ✓' % os.path.abspath(f))
        else:
            logger.error('%s: ✗' % os.path.abspath(f))

    args['files'] = files

    auth = args.get('auth')

    if auth:
        # Ask for the user password if needed
        auth = tuple(auth.split(':', 1))
        if len(auth) < 2:
            email = auth[0]
            password = getpass.getpass('Please enter a password for %s: '
                                       % email)
            auth = (email, password)

        args['auth'] = auth

    return args


def synchronize(args, local_klass, remote_klass=KintoRecords):
    """Sync local and remote collection using args.

    Take the arguments as well as a local_klass constructor a sync the
    local and remote collection.
    """

    
