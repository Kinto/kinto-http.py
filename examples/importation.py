#!/bin/bash
# -*- coding: utf-8 -*-
from kinto_client.argparse import get_parser, setup_parser, logging


def synchronize(args):
    kinto_options = {
        'server': args['host'],
        'bucket_name': args['bucket'],
        'collection_name': args['collection'],
        'auth': auth,
        'permissions': COLLECTION_PERMISSIONS
    }



def main(args=None):
    parser = get_parser(
        description="Show how to use Kinto.py utilities to build commands")
    logger = logging.getLogger(__file__)

    args = setup_parser(parser, logger)
    synchronize(args)


if __name__ == '__main__':  # pragma: nocover
    main()
