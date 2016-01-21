# -*- coding: utf-8 -*-
from __future__ import absolute_import
import argparse
import getpass
import logging
import os
from six import iteritems

from kinto_client import Client
from kinto_client.exceptions import KintoException

COMMAND_LOG_LEVEL = 25
logging.addLevelName(COMMAND_LOG_LEVEL, 'COMMAND')
logging.basicConfig(level=COMMAND_LOG_LEVEL, format="%(message)s")
global_logger = logging.getLogger(__file__)


def is_same_record(fields, one, two):
    for key in fields:
        if one.get(key) != two.get(key):
            return False
    return True


class KintoImporter(object):
    # Default configure parser values
    all_default_parameters = False
    remote_server = None
    authentication = None
    files = None
    verbosity = None

    # Remote Permissions
    bucket_permissions = None
    collection_permissions = None

    # Default values
    default_host = "http://localhost:8888/v1"
    default_bucket = None
    default_collection = None
    default_auth = None
    default_files = None

    # Sync flags
    create = True
    update = True
    delete = True

    def __init__(self, logger=None, arguments=None,
                 local_client=None, remote_client=None,
                 *args, **kwargs):
        if not hasattr(self, 'record_fields'):
            raise ValueError(
                "%r: record_fields attribute is not defined." % self)

        self.logger = logger or global_logger

        self._local_records = None
        self._remote_records = None

        parser = self.configure_parser(*args, **kwargs)
        self.args = self.get_arguments(parser, args=arguments)
        self.setup_logger()
        self.local_client = self.setup_local_client(local_client)
        self.remote_client = self.setup_remote_client(remote_client)

    def configure_parser(self, parser=None,
                         all_default_parameters=None, remote_server=None,
                         authentication=None, files=None, verbosity=None,
                         *args, **kwargs):
        """Return an argparse.ArgumentParser pre-configured object."""

        if all_default_parameters is None:
            all_default_parameters = self.all_default_parameters

        if remote_server is None:
            if self.remote_server is not None:
                remote_server = self.remote_server
            else:
                remote_server = all_default_parameters
        self.remote_server = remote_server

        if authentication is None:
            if self.authentication is not None:
                authentication = self.authentication
            else:
                authentication = all_default_parameters
        self.authentication = authentication

        if files is None:
            if self.files is not None:
                files = self.files
            else:
                files = all_default_parameters
        self.files = files

        if verbosity is None:
            if self.verbosity is not None:
                verbosity = self.verbosity
            else:
                verbosity = all_default_parameters
        self.verbosity = verbosity

        if not parser:
            parser = argparse.ArgumentParser(*args, **kwargs)

        if remote_server:
            parser.add_argument('-s', '--host', help='Kinto Server',
                                type=str, default=self.default_host)

            parser.add_argument('-b', '--bucket',
                                help='Bucket name, usually the app name',
                                type=str, default=self.default_bucket)

            parser.add_argument('-c', '--collection',
                                help='Collection name',
                                type=str, default=self.default_collection)
        if authentication:
            parser.add_argument('-u', '--auth', help='BasicAuth user:pass',
                                type=str, default=self.default_auth)

        if files:
            nargs = '+'
            if self.default_files is not None:
                nargs = '*'

            parser.add_argument('files', metavar='N', type=str, nargs=nargs,
                                help='A list of files to import.',
                                default=self.default_files)

        if verbosity:
            parser.add_argument('-v', '--verbose',
                                help='Display status',
                                dest='verbose',
                                action='store_true')

        return parser

    def get_arguments(self, parser, args=None):
        args = vars(parser.parse_args(args=args))

        files = []

        if 'files' in args:
            for f in args['files']:
                if os.path.exists(f):
                    files.append(os.path.abspath(f))
                    self.logger.log(COMMAND_LOG_LEVEL,
                                    '%s: ✓' % os.path.abspath(f))
                else:
                    self.logger.error('%s: ✗' % os.path.abspath(f))

            args['files'] = files

        auth = args.get('auth')

        if auth:
            args['auth'] = self.get_auth(auth)

        return args

    def get_auth(self, auth):
        """Ask for the user password if needed."""
        auth = tuple(auth.split(':', 1))
        if len(auth) < 2:
            email = auth[0]
            password = getpass.getpass('Please enter a password for %s: '
                                       % email)
            auth = (email, password)

        return auth

    def setup_logger(self, logger=None):
        """Configure the logger with regards to the verbosity param."""
        logger = logger or self.logger
        if 'verbose' in self.args and self.args['verbose']:
            logger.setLevel(logging.INFO)

    def get_local_records(self):
        self.logger.debug('Reading data from files')
        raise NotImplementedError()

    def setup_local_client(self, local_client=None):
        return local_client

    def setup_remote_client(self, remote_client=None):
        # If the client is already created, just return it.
        if remote_client:
            return remote_client

        # If the remote_server functionnality is not activated at the
        # parser level do not create the remote_client.
        if not self.remote_server:
            return

        # Log the endpoint where the new client will be configured.
        self.logger.log(COMMAND_LOG_LEVEL,
                        'Syncing to %s/buckets/%s/collections/%s/records' % (
                            self.args['host'].rstrip('/'),
                            self.args['bucket'],
                            self.args['collection']))

        self.remote_client = Client(server_url=self.args['host'],
                                    auth=self.args['auth'],
                                    bucket=self.args['bucket'],
                                    collection=self.args['collection'])

        # Create bucket
        # XXX: Move this to a configure
        # XXX: Add a create if not exist functionality
        try:
            self.remote_client.create_bucket(
                permissions=self.bucket_permissions)
        except KintoException as e:
            if not hasattr(e, 'response') or e.response.status_code != 412:
                raise e
        try:
            self.remote_client.create_collection(
                permissions=self.collection_permissions)
        except KintoException as e:
            if e.response.status_code != 412:
                raise e

    def get_remote_records(self):
        self.logger.log(COMMAND_LOG_LEVEL, 'Working on %r' % self.args['host'])
        return list(self.remote_client.get_records())

    @property
    def local_records(self):
        if self._local_records is None:
            _local_records = self.get_local_records()
            self._local_records = {r['id']: r for r in _local_records}
        return self._local_records

    @property
    def remote_records(self):
        if self._remote_records is None:
            _remote_records = self.get_remote_records()
            self._remote_records = {r['id']: r for r in _remote_records}
        return self._remote_records

    def sync(self, create=None, update=None, delete=None):
        """Sync local and remote collection using args.

        Take the arguments as well as a local_klass constructor a sync the
        local and remote collection.
        """
        if create is None:
            create = self.create

        if update is None:
            update = self.update

        if delete is None:
            delete = self.delete

        to_create = []
        to_update = []
        to_delete = []

        # looking at kinto to list records
        # to delete or to update
        for remote_rec_id, remote_record in iteritems(self.remote_records):
            local_record = self.local_records.get(remote_rec_id)
            if local_record is None:
                to_delete.append(remote_record)
            else:
                if not is_same_record(self.record_fields,
                                      local_record,
                                      remote_record):
                    to_update.append(local_record)

        # new records ?
        for local_record_id, local_record in iteritems(self.local_records):
            remote_record = self.remote_records.get(local_record_id)
            if not remote_record:
                to_create.append(local_record)

        if create or self.create:
            self.logger.log(COMMAND_LOG_LEVEL,
                            '- %d records will be created.' % len(to_create))
        else:
            self.logger.log(COMMAND_LOG_LEVEL,
                            '- %d records could be created.' % len(to_create))

        if update or self.update:
            self.logger.log(COMMAND_LOG_LEVEL,
                            '- %d records will be updated.' % len(to_update))
        else:
            self.logger.log(COMMAND_LOG_LEVEL,
                            '- %d records could be updated.' % len(to_update))

        if delete or self.delete:
            self.logger.log(COMMAND_LOG_LEVEL,
                            '- %d records will be deleted.' % len(to_delete))
        else:
            self.logger.log(COMMAND_LOG_LEVEL,
                            '- %d records could be deleted.' % len(to_delete))

        self.update_remote(to_create, create,
                           to_update, update,
                           to_delete, delete)

    def update_remote(self, to_create, create, to_update, update,
                      to_delete, delete):
        with self.remote_client.batch() as batch:
            if delete:
                for record in to_delete:
                    self.logger.log(COMMAND_LOG_LEVEL,
                                    '- %s: %r' % (record['id'], record))
                    batch.delete_record(record['id'])

            if update:
                for record in to_update:
                    batch.update_record(record)

            if create:
                for record in to_create:
                    batch.create_record(record)
