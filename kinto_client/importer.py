# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from kinto_client import Client
from kinto_client.exceptions import KintoException

COMMAND = 25
logging.addLevelName(COMMAND, 'COMMAND')
logging.basicConfig(level=COMMAND, format="%(message)s")


class KintoImporter(object):
    set_all = False
    bucket_permissions = None
    collection_permissions = None

    def __init__(self, *args, **kwargs):
        self._local_records = None
        self._remote_records = None

        parser = self.configure_parser(*args, **kwargs)
        self.args = self.get_arguments(parser)
        self.setup_logger(logger)
        self.setup_local_client()
        self.setup_remote_client()

    def configure_parser(parser=None, *args, **kwargs):
        """Return an argparse.ArgumentParser pre-configured object."""

        default = bool(kwargs.pop('set_all', self.set_all))
        remote_server = bool(kwargs.pop('remote_server', default))
        authentication = bool(kwargs.pop('authentication', default))
        files = bool(kwargs.pop('files', default))
        verbosity = bool(kwargs.pop('verbosity', default))

        if not parser:
            parser = argparse.ArgumentParser(*args, **kwargs)
        
        if remote_server:
            parser.add_argument('-s', '--host', help='Kinto Server',
                                type=str, default=DEFAULT_KINTO_SERVER)
    
            parser.add_argument('-b', '--bucket',
                                help='Bucket name, usually the app name',
                                type=str)

            parser.add_argument('-c', '--collection',
                                help='Collection name, usually the locale code',
                                type=str)
        if authentication:
            parser.add_argument('-u', '--auth', help='BasicAuth user:pass',
                                type=str, default=DEFAULT_USER_NAME)

        if files:
            parser.add_argument('files', metavar='N', type=str, nargs='+',
                                help='A list of properties file for the locale.')
    
        if verbosity:
            parser.add_argument('--verbose', '-v',
                                help='Display status',
                                dest='verbose',
                                action='store_true')
    
        return parser

    def get_arguments(self, parser, args=None):
        args = vars(parser.parse_args(args=args))

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

    def setup_logger(self, args, logger):
        """Configure the logger with regards to the verbosity param."""
        if self.args['verbose']:
            logger.setLevel(logging.INFO)

    def get_local_records(self):
        logger.debug('Reading data from files')
        raise NotImplemented

    def setup_local_client(self):
        pass

    def setup_remote_client(self):
        self.remote_client = Client(server_url=self.args['host'],
                                    auth=self.args['auth'],
                                    bucket=self.args['bucket'],
                                    collection=self.args['collection'])

        # Create bucket
        try:
            self.remote_client.create_bucket(
                permissions=self.bucket_permissions)
        except KintoException as e:
            if e.response.status_code != 412:
                raise e
        try:
            self.remote_client.create_collection(
                permissions=self.collection_permissions)
        except KintoException as e:
            if e.response.status_code != 412:
                raise e

    def get_remote_records(self):
        logger.log(COMMAND, 'Working on %r' % kinto_options['host'])
        return [self._kinto2rec(rec) for rec in
                self.remote_client.get_records()]


    @property
    def local_records(self):
        if not self._local_records:
            self._local_records = self.get_local_records()
        return {r['id']: r for r in}

    @property
    def kinto_records(self):
        if not self._remote_records:
            self._remote_records = self.get_remote_records()
        return {r['id']: r for r in self._remote_records}

    def sync(self, create=True, update=True, delete=True):
        """Sync local and remote collection using args.
        
        Take the arguments as well as a local_klass constructor a sync the
        local and remote collection.
        """
        logger.log(COMMAND, 'Syncing to %s/buckets/%s/collections/%s/records' % (
            self.args['host'].rstrip('/'),
            self.args['bucket'],
            self.args['collection']))

        to_create = []
        to_update = []
        to_delete = []

        # looking at kinto to list records
        # to delete or to update
        for remote_record in self.remote_records:
            local_record = self.local_records.get(remote_record['id'])
            if local_record is None:
                to_delete.append(remote_record)
            else:
                if not same_record(self.fields, local_record, remote_record):
                    to_update.append(local_record)

        # new records ?
        for record in self.local_records:
            remote_record = kinto.find(local_record['id'])
            if not remote_record:
                to_create.append(local_record)


        if create:
            logger.log(COMMAND,
                       '- %d records will be created.' % len(to_create))
        else:
            logger.log(COMMAND,
                       '- %d records could be created.' % len(to_create))

        if update:
            logger.log(COMMAND,
                       '- %d records will be updated.' % len(to_update))
        else:
            logger.log(COMMAND,
                       '- %d records could be updated.' % len(to_update))
            
            
        if delete:
            logger.log(COMMAND,
                       '- %d records will be deleted.' % len(to_delete))
        else:
            logger.log(COMMAND,
                       '- %d records could be deleted.' % len(to_delete))


        self.update_remote(to_create, create,
                           to_update, update,
                           to_delete, delete)

    def update_remote(self, to_create, create, to_update, update,
                      to_delete, delete):
        with self.client.batch() as batch:
            if delete:
                for record in to_delete:
                    logger.log(COMMAND, '- %s: %r' % (record['id'], record))
                    batch.delete(record)

            if update:
                for record in to_update:
                    batch.create(record)

            if create:
                for record in to_create:
                    batch.create(record)

        batch.send()
