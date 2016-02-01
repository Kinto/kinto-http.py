import argparse
import logging

from kinto_client import Client
from kinto_client import exceptions

logger = logging.getLogger(__name__)


def replicate(origin, destination):
    """Replicates all the information from one server to another one.

    The passed settings should match the named parameters of the python client.
    """
    msg = 'Replication from {0} to {1}'.format(origin, destination)
    logger.info(msg)

    try:
        destination.get_bucket()
    except exceptions.BucketNotFound:
        destination.create_bucket()
    try:
        destination.get_collection()
    except exceptions.KintoException:
        collection_data = origin.get_collection()
        destination.create_collection(
            data=collection_data['data'],
            permissions=collection_data['permissions'], safe=False)
    # XXX Why safe=False?

    records = origin.get_records()
    logger.info('replication of {0} records'.format(len(records)))
    with destination.batch() as batch:
        for record in records:
            if record.get('deleted', False) is True:
                batch.delete_record(record['id'],
                                    last_modified=record['last_modified'])
            else:
                batch.update_record(data=record, safe=False)


def get_arguments():  # pragma: nocover
    description = 'Migrate data from one kinto instance to another one.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('origin_server',
                        help='The location of the origin server (with prefix)')
    parser.add_argument('destination_server',
                        help=('The location of the destination server '
                              '(with prefix)'))
    parser.add_argument('bucket', help='The name of the bucket')
    parser.add_argument('collection', help='The name of the collection')

    # Auth: XXX improve later. For now only support Basic Auth.
    parser.add_argument('-a', '--auth', dest='auth',
                        help='Authentication, in the form "username:password"')

    # Optional arguments. They will be derivated from the "bucket"
    # and "collection" ones.
    parser.add_argument('--destination-bucket', dest='destination_bucket',
                        help='The name of the destination bucket',
                        default=None)
    parser.add_argument('--destination-collection',
                        dest='destination_collection',
                        help='The name of the destination bucket',
                        default=None)

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
    return parser.parse_args()


def setup_logger(args):  # pragma: nocover
    logger.addHandler(logging.StreamHandler())
    if args.verbosity:
        logger.setLevel(args.verbosity)


def main():  # pragma: nocover
    args = get_arguments()
    setup_logger(args)

    auth = tuple(args.auth.split(':')) if args.auth else None

    origin = Client(
        server_url=args.origin_server,
        auth=auth,
        bucket=args.bucket,
        collection=args.collection
    )
    destination = Client(
        server_url=args.destination_server,
        auth=auth,
        bucket=args.destination_bucket or args.bucket,
        collection=args.destination_collection or args.collection
    )

    replicate(origin, destination)


if __name__ == "__main__":  # pragma: nocover
    main()
