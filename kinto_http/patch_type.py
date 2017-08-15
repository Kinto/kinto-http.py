class PatchType(object):
    """Class representing a PATCH request to Kinto.

    Kinto understands different PATCH requests, which can be
    represented by subclasses of this class.
    """
    pass

class BasicPatch(PatchType):
    """Class representing a default "attribute merge" PATCH.

    In this kind of patch, attributes in the request replace
    attributes in the original object.

    This kind of PATCH is documented at e.g.
    http://docs.kinto-storage.org/en/stable/api/1.x/records.html#attributes-merge.
    """

    content_type = 'application/json'

    def __init__(self, data):
        """BasicPatch(data)

        :param data: the fields and values that should be replaced
        :type data: dict
        """
        self.body = data


class MergePatch(PatchType):
    """Class representing a "JSON merge".

    In this kind of patch, JSON objects are merged recursively, and
    setting a field to None will remove it from the original object.

    This kind of PATCH is documented at e.g.
    http://docs.kinto-storage.org/en/stable/api/1.x/records.html?highlight=JSON%20merge#attributes-merge.
    """

    content_type = 'application/merge-patch+json'

    def __init__(self, data):
        """MergePatch(data)

        :param data: the fields and values that should be merged
        :type data: dict
        """
        self.body = data


class JSONPatch(PatchType):
    """Class representing a JSON Patch PATCH.

    In this kind of patch, a set of operations are sent to the server,
    which applies them in order.

    This kind of PATCH is documented at e.g.
    http://docs.kinto-storage.org/en/stable/api/1.x/records.html#json-patch-operations.
    """

    content_type = 'application/json-patch+json'

    def __init__(self, operations):
        """JSONPatch(operations)

        :param operations: the operations that should be performed, as dicts
        :type operations: list
        """
        self.body = operations
