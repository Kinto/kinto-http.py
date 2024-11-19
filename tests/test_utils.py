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


def test_sort_single_field_ascending():
    records = [
        {"name": "Charlie", "age": 25},
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 20},
    ]
    result = utils.sort_records(records, "name")
    expected = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 20},
        {"name": "Charlie", "age": 25},
    ]
    assert result == expected


def test_sort_single_field_descending():
    records = [
        {"name": "Charlie", "age": 25},
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 20},
    ]
    result = utils.sort_records(records, "-name")
    expected = [
        {"name": "Charlie", "age": 25},
        {"name": "Bob", "age": 20},
        {"name": "Alice", "age": 30},
    ]
    assert result == expected


def test_sort_multiple_fields():
    records = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Alice", "age": 20},
    ]
    result = utils.sort_records(records, "name,-age")
    expected = [
        {"name": "Alice", "age": 30},
        {"name": "Alice", "age": 20},
        {"name": "Bob", "age": 25},
    ]
    assert result == expected


def test_sort_missing_field():
    records = [
        {"name": "Charlie", "age": 25},
        {"name": "Alice"},
        {"name": "Bob", "age": 20},
    ]
    result = utils.sort_records(records, "age")
    expected = [
        {"name": "Bob", "age": 20},
        {"name": "Charlie", "age": 25},
        {"name": "Alice"},  # Missing "age" is treated as default
    ]
    assert result == expected


def test_sort_numeric_field_descending():
    records = [
        {"name": "Charlie", "score": 85},
        {"name": "Alice", "score": 95},
        {"name": "Bob", "score": 111},
    ]
    result = utils.sort_records(records, "-score")
    expected = [
        {"name": "Bob", "score": 111},
        {"name": "Alice", "score": 95},
        {"name": "Charlie", "score": 85},
    ]
    assert result == expected


def test_sort_mixed_numeric_and_string():
    records = [
        {"name": "Charlie", "age": 25},
        {"name": "Alice", "age": 20},
        {"name": "Bob", "age": 20},
    ]
    result = utils.sort_records(records, "age,-name")
    expected = [
        {"name": "Bob", "age": 20},
        {"name": "Alice", "age": 20},
        {"name": "Charlie", "age": 25},
    ]
    assert result == expected


def test_records_equal_identical_records():
    a = {"id": 1, "name": "Alice", "last_modified": 123, "schema": "v1"}
    b = {"id": 1, "name": "Alice", "last_modified": 456, "schema": "v2"}
    assert utils.records_equal(a, b)


def test_records_equal_different_records():
    a = {"id": 1, "name": "Alice", "last_modified": 123}
    b = {"id": 2, "name": "Bob", "last_modified": 456}
    assert not utils.records_equal(a, b)


def test_records_equal_missing_fields():
    a = {"id": 1, "name": "Alice", "last_modified": 123}
    b = {"id": 1, "name": "Alice"}
    assert utils.records_equal(a, b)


def test_records_equal_extra_fields():
    a = {"id": 1, "name": "Alice", "extra": "field"}
    b = {"id": 1, "name": "Alice"}
    assert not utils.records_equal(a, b)


def test_records_equal_empty_records():
    a = {}
    b = {}
    assert utils.records_equal(a, b)


def test_records_equal_only_ignored_fields():
    a = {"last_modified": 123, "schema": "v1"}
    b = {"last_modified": 456, "schema": "v2"}
    assert utils.records_equal(a, b)
