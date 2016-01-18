# -*- coding: utf-8 -*-
from unittest2 import TestCase

from kinto_client import utils


class UtilsTest(TestCase):

    def test_slugify_converts_integers(self):
        assert utils.slugify(1) == '1'

    def test_slugify_replaces_spaces_by_hyphens(self):
        assert utils.slugify(u'text with spaces') == 'text-with-spaces'

    def test_slugify_removes_unknown_characters(self):
        assert utils.slugify(u'chars!') == 'chars'

    def test_slugify_replaces_equivalent_chars(self):
        assert utils.slugify(u'chârs') == 'chars'

    def test_slugify_do_no_modify_valid_ids(self):
        for value in ['en-US', 'en_GB']:
            assert utils.slugify(value) == value

    def test_urljoin_can_join_with_trailing_slash(self):
        url = utils.urljoin("http://localhost/", "v1")
        self.assertEquals(url, "http://localhost/v1")

    def test_urljoin_can_join_with_prepend_slash(self):
        url = utils.urljoin("http://localhost", "/v1")
        self.assertEquals(url, "http://localhost/v1")

    def test_urljoin_can_join_with_both_trailing_and_prepend_slash(self):
        url = utils.urljoin("http://localhost/", "/v1")
        self.assertEquals(url, "http://localhost/v1")

    def test_urljoin_can_join_prefixed_server_url(self):
        url = utils.urljoin("http://localhost/v1/", "/tests")
        self.assertEquals(url, "http://localhost/v1/tests")

    def test_urljoin_can_join_without_trailing_nor_prepend_slash(self):
        url = utils.urljoin("http://localhost", "v1")
        self.assertEquals(url, "http://localhost/v1")
