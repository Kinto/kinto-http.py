from typing import Dict, Tuple

import pytest

from kinto_http import KintoException
from kinto_http.endpoints import Endpoints


def test_root(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("root", **kwargs) == "/"


def test_batch(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("batch", **kwargs) == "/batch"


def test_buckets(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("buckets", **kwargs) == "/buckets"


def test_bucket(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("bucket", **kwargs) == "/buckets/buck"


def test_collections(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("collections", **kwargs) == "/buckets/buck/collections"


def test_collection(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("collection", **kwargs) == "/buckets/buck/collections/coll"


def test_records(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("records", **kwargs) == "/buckets/buck/collections/coll/records"


def test_record(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("record", **kwargs) == "/buckets/buck/collections/coll/records/1"


def test_history(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, kwargs = endpoints_setup
    assert endpoints.get("history", **kwargs) == "/buckets/buck/history"


def test_missing_arguments_raise_an_error(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, _ = endpoints_setup
    # Don't include the record id; it should raise an error.
    with pytest.raises(KintoException) as context:
        endpoints.get("record", bucket="buck", collection="coll")
    msg = "Cannot get record endpoint, id is missing"
    assert msg in str(context.value)


def test_null_arguments_raise_an_error(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, _ = endpoints_setup
    # Include a null record id; it should raise an error.
    with pytest.raises(KintoException) as context:
        endpoints.get("record", bucket="buck", collection="coll", id=None)
    msg = "Cannot get record endpoint, id is missing"
    assert msg in str(context.value)


def test_arguments_are_slugified(endpoints_setup: Tuple[Endpoints, Dict]):
    endpoints, _ = endpoints_setup
    assert endpoints.get("bucket", bucket="My Bucket") == "/buckets/my-bucket"
