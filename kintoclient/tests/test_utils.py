# -*- coding: utf-8 -*-
from unittest2 import TestCase

from kintoclient import utils


class UtilsTest(TestCase):

    def test_slugify_replaces_spaces_by_hyphens(self):
        assert utils.slugify(u'text with spaces') == 'text-with-spaces'

    def test_slugify_removes_unknown_characters(self):
        assert utils.slugify(u'chars!') == 'chars'

    def test_slugify_replaces_equivalent_chars(self):
        assert utils.slugify(u'chârs') == 'chars'
