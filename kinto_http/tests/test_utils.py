from kinto_http import utils


def test_slugify_converts_integers():
    assert utils.slugify(1) == "1"


def test_slugify_replaces_spaces_by_hyphens():
    assert utils.slugify("text with spaces") == "text-with-spaces"


def test_slugify_removes_unknown_characters():
    assert utils.slugify("chars!") == "chars"


def test_slugify_replaces_equivalent_chars():
    assert utils.slugify("chârs") == "chars"


def test_slugify_do_no_modify_valid_ids():
    for value in ["en-US", "en_GB"]:
        assert utils.slugify(value) == value


def test_urljoin_can_join_with_trailing_slash():
    url = utils.urljoin("http://localhost/", "v1")
    assert url == "http://localhost/v1"


def test_urljoin_can_join_with_prepend_slash():
    url = utils.urljoin("http://localhost", "/v1")
    assert url == "http://localhost/v1"


def test_urljoin_can_join_with_both_trailing_and_prepend_slash():
    url = utils.urljoin("http://localhost/", "/v1")
    assert url == "http://localhost/v1"


def test_urljoin_can_join_prefixed_server_url():
    url = utils.urljoin("http://localhost/v1/", "/tests")
    assert url == "http://localhost/v1/tests"


def test_urljoin_can_join_without_trailing_nor_prepend_slash():
    url = utils.urljoin("http://localhost", "v1")
    assert url == "http://localhost/v1"


def test_quote_strips_extra_quotes():
    assert utils.quote('"1234"') == '"1234"'


def test_quotes_can_take_integers():
    assert utils.quote(1234) == '"1234"'
