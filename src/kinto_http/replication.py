import argparse
import logging

from kinto_http import Client, cli_utils


logger = logging.getLogger(__name__)


def replicate(origin, destination):
    """Replicates records from one collection to another one.

    All records are replicated, not only the ones that changed.
    """
    msg = "Replication from {0} to {1}".format(origin, destination)
    logger.info(msg)

    destination.create_bucket(if_not_exists=True)
    collection_data = origin.get_collection()
    destination.create_collection(
        data=collection_data["data"],
        permissions=collection_data["permissions"],
        if_not_exists=True,
    )

    records = origin.get_records()
    logger.info("replication of {0} records".format(len(records)))
    with destination.batch() as batch:
        for record in records:
            if record.get("deleted", False) is True:
                batch.delete_record(record["id"], last_modified=record["last_modified"])
            else:
                batch.update_record(data=record, safe=False)


def get_arguments():  # pragma: nocover
    description = "Migrate data from one kinto instance to another one."
    parser = argparse.ArgumentParser(description=description)

    # Optional arguments. They will be derivated from the remote ones.
    parser.add_argument("-o", "--origin", help="The location of the origin server (with prefix)")

    parser.add_argument(
        "--origin-auth",
        help="The origin authentication credentials. Will use the same as the remote if omitted",
        action=cli_utils.AuthAction,
        default=None,
    )

    parser.add_argument(
        "--origin-bucket",
        dest="origin_bucket",
        help="The name of the origin bucket. Will use the same as the remote if omitted",
        default=None,
    )

    parser.add_argument(
        "--origin-collection",
        dest="origin_collection",
        help="The name of the origin collection. Will use the same as the remote if omitted",
        default=None,
    )
    cli_utils.set_parser_server_options(parser)
    return parser.parse_args()


def main():  # pragma: nocover
    args = get_arguments()
    cli_utils.setup_logger(logger, args)

    origin = Client(
        server_url=args.origin_server,
        auth=args.origin_auth or args.auth,
        bucket=args.origin_bucket or args.bucket,
        collection=args.origin_collection or args.collection,
    )
    destination = cli_utils.create_client_from_args(args)

    replicate(origin, destination)


if __name__ == "__main__":  # pragma: nocover
    main()
