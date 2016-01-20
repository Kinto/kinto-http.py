#!/usr/bin/env python
# -*- coding: utf-8 -*-
from kinto_client.importer import KintoImporter


class DummyImporter(KintoImporter):
    all_default_parameters = True
    collection_permissions = {'read': ["system.Everyone"]}
    fields = ('name', 'protocol')

    def get_local_records(self):
        return [
            {'id': "f3a31016-274b-a558-6e21-d1a00f74090f",
             'name': "websocket",
             'protocol': "ws"},
            {'id': "2e6e434b-eac6-f84f-0905-e9f9bb7ab5ab",
             'name': "IRC",
             'protocol': "irc"},
            {'id': "ba87a851-fe45-5a57-f238-d4fbc832ea30",
             'name': "HTTP",
             'protocol': "http"},
            {'id': "106b1b39-071f-dc61-e4e3-7e5b1063a5b2",
             'name': "Mail",
             'protocol': "mailto"},
        ]


def main(args=None):
    importer = DummyImporter()
    importer.sync(delete=False)


if __name__ == '__main__':  # pragma: nocover
    main()
