import argparse
import logging
logger = logging.getLogger(__name__)

from kinto_client import Client


def replicate(origin_settings, destination_settings):
    """Replicates all the information from one server to another one.

    The passed settings should match the named parameters of the python client.
    """
    msg = 'Replication from {0} to {1}'.format(
        '{server_url}/{bucket}/{collection}'.format(**origin_settings),
        '{server_url}/{bucket}/{collection}'.format(**destination_settings)
    )
    logger.info(msg)

    origin = Client(**origin_settings)
    destination = Client(**destination_settings)

    # XXX Since records list don't include metadata (permissions). Need to get
    # each individual record instead using read-batching.
    # For now, since we don't need to sync the permissions, retrieve everything
    # with get_records().
    with destination.batch() as batch:
        # XXX Support batch limitations.
        records = origin.get_records()
        logger.info('replication of {0} records'.format(len(records)))
        for record in records:
            # XXX Add permissions.
            batch.update_record(data=record)

        bucket_data = origin.get_bucket()
        batch.update_bucket(
            data=bucket_data['data'],
            permissions=bucket_data['permissions'])

        collection_data = origin.get_collection()
        batch.update_collection(
            data=collection_data['data'],
            permissions=collection_data['permissions'])


def get_arguments():
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


def setup_logger(args):
    logger.addHandler(logging.StreamHandler())
    if args.verbosity:
        logger.setLevel(args.verbosity)


def main():
    args = get_arguments()
    setup_logger(args)

    auth = tuple(args.auth.split(':')) if args.auth else None

    replicate(
        origin_settings={
            'server_url': args.origin_server,
            'auth': auth,
            'bucket': args.bucket,
            'collection': args.collection
        },
        destination_settings={
            'server_url': args.destination_server,
            'auth': auth,
            'bucket': args.destination_bucket or args.bucket,
            'collection': args.destination_collection or args.collection
        }
    )


if __name__ == "__main__":
    main()
