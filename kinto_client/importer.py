# -*- coding: utf-8 -*-
from __future__ import absolute_import
import argparse
import getpass
import os
from six import iteritems

from kinto_client import Client
from kinto_client.exceptions import KintoException
from kinto_client.logging import logging, global_logger, command_log


def is_same_record(fields, one, two):
    for key in fields:
        if one.get(key) != two.get(key):
            return False
    return True


class KintoImporter(object):
    # Default configure parser values
    """Configure the parser with all parameters."""
    include_all_default_parameters = False
    """Configure the parser to allow remote_server configuration."""
    include_remote_server = None
    """Configure the parser to allow authentication configuration."""
    include_authentication = None
    """Configure the parser to allow files selection."""
    include_files = None
    """Configure the parser to allow verbosity configuration."""
    include_verbosity = None

    # Default values
    """Default value for the remote server host value."""
    default_host = "http://localhost:8888/v1"
    """Default bucket name for the remote server."""
    default_bucket = None
    """Default collection name for the remote server."""
    default_collection = None
    """Default authentication credentials for the remote server."""
    default_auth = None
    """Default files to load for the local records."""
    default_files = None

    # Remote Permissions
    """Remote bucket permissions on bucket creation."""
    bucket_permissions = None
    """Remote collection permission on collection creation."""
    collection_permissions = None

    # Sync flags
    """Create new records."""
    create = True
    """Update out-of-date records."""
    update = True
    """Delete records not present in local-files."""
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
                         include_all_default_parameters=None,
                         include_remote_server=None,
                         include_authentication=None,
                         include_files=None,
                         include_verbosity=None,
                         *args, **kwargs):
        """Return an argparse.ArgumentParser pre-configured object.
        :param argparse.ArgumentParser parser:
            The parser to configure. Set to None it will create a new parser.

        :param boolean include_all_default_parameters:
            Configure the default for parameters defined below.
            It is False by default. I can also be defined as a class attribute.

        :param boolean include_remote_server:
            Allow remote server credentials:
                --host:       The remote server host.
                --bucket:     The bucket ID.
                --collection: The collection ID.

        :param boolean include_authentication: Allow authentication credentials
            Allow authentication management:
                --auth token:my-secret
                --auth token  # Will ask for the password on STDIN

        :param boolean include_files:
            Allow input files for local_records loading (can be a list
            of files)

        :param boolean include_verbosity: Allow verbosity configuration
            Configure the log level to logging.INFO

        Extra args and kwargs are pass through to the ArgumentParser
        object constructor, in case parser has to be created.

        """

        if include_all_default_parameters is None:
            include_all_default_parameters = (
                self.include_all_default_parameters)

        if include_remote_server is None:
            if self.include_remote_server is not None:
                include_remote_server = self.include_remote_server
            else:
                include_remote_server = include_all_default_parameters
        self.include_remote_server = include_remote_server

        if include_authentication is None:
            if self.include_authentication is not None:
                include_authentication = self.include_authentication
            else:
                include_authentication = include_all_default_parameters
        self.include_authentication = include_authentication

        if include_files is None:
            if self.include_files is not None:
                include_files = self.include_files
            else:
                include_files = include_all_default_parameters
        self.include_files = include_files

        if include_verbosity is None:
            if self.include_verbosity is not None:
                include_verbosity = self.include_verbosity
            else:
                include_verbosity = include_all_default_parameters
        self.include_verbosity = include_verbosity

        if not parser:
            parser = argparse.ArgumentParser(*args, **kwargs)

        if include_remote_server:
            parser.add_argument('-s', '--host', help='Kinto Server',
                                type=str, default=self.default_host)

            parser.add_argument('-b', '--bucket',
                                help='Bucket name, usually the app name',
                                type=str, default=self.default_bucket)

            parser.add_argument('-c', '--collection',
                                help='Collection name',
                                type=str, default=self.default_collection)
        if include_authentication:
            parser.add_argument('-u', '--auth',
                                help='BasicAuth token:my-secret',
                                type=str, default=self.default_auth)

        if include_files:
            nargs = '+'
            if self.default_files is not None:
                nargs = '*'

            parser.add_argument('files', metavar='N', type=str, nargs=nargs,
                                help='A list of files to import.',
                                default=self.default_files)

        if include_verbosity:
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
                    command_log(self.logger, '%s: ✓' % os.path.abspath(f))
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
        # If the client is specified, just return it.
        if remote_client:
            return remote_client

        # If the include_remote_server functionnality is not activated at the
        # parser level do not create the remote_client.
        if not self.include_remote_server:
            return

        # Log the endpoint where the new client will be configured.
        command_log(
            self.logger,
            'Syncing to %s/buckets/%s/collections/%s/records' % (
                self.args['host'].rstrip('/'),
                self.args['bucket'],
                self.args['collection']))

        remote_client = Client(server_url=self.args['host'],
                               auth=self.args['auth'],
                               bucket=self.args['bucket'],
                               collection=self.args['collection'])

        # Create bucket
        # XXX: Move this to a configure (Refs #41)
        # XXX: Add a create if not exist functionality (Refs #42)
        try:
            remote_client.create_bucket(
                permissions=self.bucket_permissions)
        except KintoException as e:
            if not hasattr(e, 'response') or e.response.status_code != 412:
                raise e
        try:
            remote_client.create_collection(
                permissions=self.collection_permissions)
        except KintoException as e:
            if e.response.status_code != 412:
                raise e

        return remote_client

    def get_remote_records(self):
        command_log(self.logger, 'Working on %r' % self.args['host'])
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

        Take the arguments as well as a ``local_klass`` constructor a
        sync the local and remote collection.

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
            command_log(self.logger,
                        '- %d records will be created.' % len(to_create))
        else:
            command_log(self.logger,
                        '- %d records could be created.' % len(to_create))

        if update or self.update:
            command_log(self.logger,
                        '- %d records will be updated.' % len(to_update))
        else:
            command_log(self.logger,
                        '- %d records could be updated.' % len(to_update))

        if delete or self.delete:
            command_log(self.logger,
                        '- %d records will be deleted.' % len(to_delete))
        else:
            command_log(self.logger,
                        '- %d records could be deleted.' % len(to_delete))

        self.update_remote(to_create, create,
                           to_update, update,
                           to_delete, delete)

    def update_remote(self, to_create, create, to_update, update,
                      to_delete, delete):
        with self.remote_client.batch() as batch:
            if delete:
                for record in to_delete:
                    command_log(self.logger,
                                '- %s: %r' % (record['id'], record))
                    batch.delete_record(record['id'])

            if update:
                for record in to_update:
                    batch.update_record(record)

            if create:
                for record in to_create:
                    batch.create_record(record)
