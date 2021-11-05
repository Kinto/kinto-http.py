import asyncio
import logging
import random
from typing import Dict, List

import backoff
import requests

from kinto_http import Client, utils


logger = logging.getLogger(__name__)

retry_timeout = backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=2,
)


class AsyncClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = Client(*args, **kwargs)

    def clone(self, **kwargs):
        if "server_url" in kwargs or "auth" in kwargs:
            kwargs.setdefault("server_url", self.session.server_url)
            kwargs.setdefault("auth", self.session.auth)
        else:
            kwargs.setdefault("session", self.session)
        kwargs.setdefault("bucket", self._bucket_name)
        kwargs.setdefault("collection", self._collection_name)
        kwargs.setdefault("retry", self.session.nb_retry)
        kwargs.setdefault("retry_after", self.session.retry_after)
        return AsyncClient(**kwargs)

    @retry_timeout
    async def server_info(self) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.server_info())

    @retry_timeout
    async def get_bucket(self, *, id=None, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_bucket(id=id, **kwargs))

    @retry_timeout
    async def get_buckets(self, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_buckets(**kwargs))

    @retry_timeout
    async def create_bucket(
        self, *, id=None, data=None, permissions=None, safe=True, if_not_exists=False
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.create_bucket(
                id=id, data=data, permissions=permissions, safe=safe, if_not_exists=if_not_exists
            ),
        )

    @retry_timeout
    async def update_bucket(
        self, *, id=None, data=None, permissions=None, safe=True, if_match=None
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.update_bucket(
                id=id, data=data, permissions=permissions, safe=safe, if_match=if_match
            ),
        )

    @retry_timeout
    async def patch_bucket(
        self,
        *,
        id=None,
        changes=None,
        data=None,
        original=None,
        permissions=None,
        safe=True,
        if_match=None,
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.patch_bucket(
                id=id,
                changes=changes,
                data=data,
                original=original,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def delete_bucket(self, *, id=None, safe=True, if_match=None, if_exists=False) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.delete_bucket(
                id=id, safe=safe, if_match=if_match, if_exists=if_exists
            ),
        )

    @retry_timeout
    async def delete_buckets(self, *, safe=True, if_match=None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_buckets(safe=safe, if_match=if_match)
        )

    @retry_timeout
    async def get_group(self, *, id, bucket=None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_group(id=id, bucket=bucket)
        )

    @retry_timeout
    async def get_groups(self, *, bucket=None, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_groups(bucket=bucket, **kwargs)
        )

    @retry_timeout
    async def create_group(
        self, *, id=None, bucket=None, data=None, permissions=None, safe=True, if_not_exists=False
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.create_group(
                id=id,
                bucket=bucket,
                data=data,
                permissions=permissions,
                safe=safe,
                if_not_exists=if_not_exists,
            ),
        )

    @retry_timeout
    async def update_group(
        self, *, id=None, bucket=None, data=None, permissions=None, safe=True, if_match=None
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.update_group(
                id=id,
                bucket=bucket,
                data=data,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def patch_group(
        self,
        *,
        id=None,
        bucket=None,
        changes=None,
        data=None,
        original=None,
        permissions=None,
        safe=True,
        if_match=None,
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.patch_group(
                id=id,
                bucket=bucket,
                changes=changes,
                data=data,
                original=original,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def delete_group(
        self, *, id, bucket=None, safe=True, if_match=None, if_exists=False
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.delete_group(
                id=id, bucket=bucket, safe=safe, if_match=if_match, if_exists=if_exists
            ),
        )

    @retry_timeout
    async def delete_groups(self, *, bucket=None, safe=True, if_match=None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_groups(bucket=bucket, safe=safe, if_match=if_match)
        )

    @retry_timeout
    async def get_collection(self, *, id=None, bucket=None, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_collection(id=id, bucket=bucket, **kwargs)
        )

    @retry_timeout
    async def get_collections(self, *, bucket=None, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_collections(bucket=bucket, **kwargs)
        )

    @retry_timeout
    async def create_collection(
        self, *, id=None, bucket=None, data=None, permissions=None, safe=True, if_not_exists=False
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.create_collection(
                id=id,
                bucket=bucket,
                data=data,
                permissions=permissions,
                safe=safe,
                if_not_exists=if_not_exists,
            ),
        )

    @retry_timeout
    async def update_collection(
        self, *, id=None, bucket=None, data=None, permissions=None, safe=True, if_match=None
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.update_collection(
                id=id,
                bucket=bucket,
                data=data,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def patch_collection(
        self,
        *,
        id=None,
        bucket=None,
        changes=None,
        data=None,
        original=None,
        permissions=None,
        safe=True,
        if_match=None,
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.patch_collection(
                id=id,
                bucket=bucket,
                changes=changes,
                data=data,
                original=original,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def delete_collection(
        self, *, id=None, bucket=None, safe=True, if_match=None, if_exists=False
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.delete_collection(
                id=id, bucket=bucket, safe=safe, if_match=if_match, if_exists=if_exists
            ),
        )

    @retry_timeout
    async def delete_collections(self, *, bucket=None, safe=True, if_match=None) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.delete_collections(bucket=bucket, safe=safe, if_match=if_match),
        )

    @retry_timeout
    async def get_record(self, *, id, collection=None, bucket=None, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.get_record(id=id, collection=collection, bucket=bucket, **kwargs),
        )

    @retry_timeout
    async def get_records(self, *, collection=None, bucket=None, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_records(collection=collection, bucket=bucket, **kwargs)
        )

    @retry_timeout
    async def get_paginated_records(self, *, collection=None, bucket=None, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.get_paginated_records(
                collection=collection, bucket=bucket, **kwargs
            ),
        )

    @retry_timeout
    async def get_records_timestamp(self, *, collection=None, bucket=None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_records_timestamp(collection=collection, bucket=bucket)
        )

    @retry_timeout
    async def create_record(
        self,
        *,
        id=None,
        bucket=None,
        collection=None,
        data=None,
        permissions=None,
        safe=True,
        if_not_exists=False,
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.create_record(
                id=id,
                bucket=bucket,
                collection=collection,
                data=data,
                permissions=permissions,
                safe=safe,
                if_not_exists=if_not_exists,
            ),
        )

    @retry_timeout
    async def update_record(
        self,
        *,
        id=None,
        collection=None,
        bucket=None,
        data=None,
        permissions=None,
        safe=True,
        if_match=None,
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.update_record(
                id=id,
                collection=collection,
                bucket=bucket,
                data=data,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def patch_record(
        self,
        *,
        id=None,
        collection=None,
        bucket=None,
        changes=None,
        data=None,
        original=None,
        permissions=None,
        safe=True,
        if_match=None,
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.patch_record(
                id=id,
                collection=collection,
                bucket=bucket,
                changes=changes,
                data=data,
                original=original,
                permissions=permissions,
                safe=safe,
                if_match=if_match,
            ),
        )

    @retry_timeout
    async def delete_record(
        self, *, id, collection=None, bucket=None, safe=True, if_match=None, if_exists=False
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.delete_record(
                id=id,
                collection=collection,
                bucket=bucket,
                safe=safe,
                if_match=if_match,
                if_exists=if_exists,
            ),
        )

    @retry_timeout
    async def delete_records(
        self, *, collection=None, bucket=None, safe=True, if_match=None
    ) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.delete_records(
                collection=collection, bucket=bucket, safe=safe, if_match=if_match
            ),
        )

    @retry_timeout
    async def get_history(self, *, bucket=None, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_history(bucket=bucket, **kwargs)
        )

    @retry_timeout
    async def purge_history(self, *, bucket=None, safe=True, if_match=None) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.purge_history(bucket=bucket, safe=safe, if_match=if_match)
        )

    @retry_timeout
    async def get_endpoint(
        self, name, *, bucket=None, group=None, collection=None, id=None
    ) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.get_endpoint(
                name, bucket=bucket, group=group, collection=collection, id=id
            ),
        )

    @retry_timeout
    async def get_monitor_changes(self, bust_cache=False, **kwargs) -> List[Dict]:
        if bust_cache:
            if "_expected" in kwargs:
                raise ValueError("Pick one of `bust_cache` and `_expected` parameters")
            random_cache_bust = random.randint(999999000000, 999999999999)
            kwargs["_expected"] = random_cache_bust
        return await self.get_records(bucket="monitor", collection="changes", **kwargs)

    # TODO: get proper tests written for this
    # @retry_timeout
    # async def get_changeset(self, bucket, collection, **kwargs) -> List[Dict]:
    #     endpoint = f"/buckets/{bucket}/collections/{collection}/changeset"
    #     kwargs.setdefault("_expected", random.randint(999999000000, 999999999999))
    #     loop = asyncio.get_event_loop()
    #     body, _ = await loop.run_in_executor(
    #         None, lambda: self._client.session.request("get", endpoint, params=kwargs)
    #     )
    #     return body

    def __repr__(self):
        if self._collection_name:
            endpoint = self._client.get_endpoint(
                "collection", bucket=self._bucket_name, collection=self._collection_name
            )
        elif self._bucket_name:
            endpoint = self._client.get_endpoint("bucket", bucket=self._bucket_name)
        else:
            endpoint = self._client.get_endpoint("root")

        absolute_endpoint = utils.urljoin(self.session.server_url, endpoint)
        return f"<KintoClient {absolute_endpoint}>"
