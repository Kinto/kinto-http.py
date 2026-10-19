from kinto_http.patch_type import BasicPatch, JSONPatch, MergePatch, PatchType


def test_base_patch_type_has_empty_body():
    assert PatchType().body is None


def test_basic_patch_body_omits_missing_fields():
    assert BasicPatch(data={"foo": "bar"}).body == {"data": {"foo": "bar"}}


def test_merge_patch_body_contains_data_and_permissions():
    patch = MergePatch(data={"foo": "bar"}, permissions={"read": ["alice"]})
    assert patch.body == {"data": {"foo": "bar"}, "permissions": {"read": ["alice"]}}


def test_json_patch_body_is_the_list_of_operations():
    operations = [{"op": "add", "path": "/data/foo", "value": "bar"}]
    assert JSONPatch(operations).body == operations
