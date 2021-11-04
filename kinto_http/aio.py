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
    async def server_info(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.server_info(*args, **kwargs))

    @retry_timeout
    async def get_bucket(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_bucket(*args, **kwargs))

    @retry_timeout
    async def get_buckets(self, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_buckets(**kwargs))

    @retry_timeout
    async def create_bucket(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.create_bucket(*args, **kwargs)
        )

    @retry_timeout
    async def update_bucket(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.update_bucket(*args, **kwargs)
        )

    @retry_timeout
    async def patch_bucket(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.patch_bucket(*args, **kwargs))

    @retry_timeout
    async def delete_bucket(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_bucket(*args, **kwargs)
        )

    @retry_timeout
    async def delete_buckets(self, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.delete_buckets(**kwargs))

    @retry_timeout
    async def get_group(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_group(*args, **kwargs))

    @retry_timeout
    async def get_groups(self, *args, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_groups(*args, **kwargs))

    @retry_timeout
    async def create_group(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.create_group(*args, **kwargs))

    @retry_timeout
    async def update_group(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.update_group(*args, **kwargs))

    @retry_timeout
    async def patch_group(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.patch_group(*args, **kwargs))

    @retry_timeout
    async def delete_group(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.delete_group(*args, **kwargs))

    @retry_timeout
    async def delete_groups(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_groups(*args, **kwargs)
        )

    @retry_timeout
    async def get_collection(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_collection(*args, **kwargs)
        )

    @retry_timeout
    async def get_collections(self, *args, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_collections(*args, **kwargs)
        )

    @retry_timeout
    async def create_collection(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.create_collection(*args, **kwargs)
        )

    @retry_timeout
    async def update_collection(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.update_collection(*args, **kwargs)
        )

    @retry_timeout
    async def patch_collection(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.patch_collection(*args, **kwargs)
        )

    @retry_timeout
    async def delete_collection(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_collection(*args, **kwargs)
        )

    @retry_timeout
    async def delete_collections(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_collections(*args, **kwargs)
        )

    @retry_timeout
    async def get_record(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_record(*args, **kwargs))

    @retry_timeout
    async def get_records(self, *args, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_records(*args, **kwargs))

    @retry_timeout
    async def get_paginated_records(self, *args, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_paginated_records(*args, **kwargs)
        )

    @retry_timeout
    async def get_records_timestamp(self, *args, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.get_records_timestamp(*args, **kwargs)
        )

    @retry_timeout
    async def create_record(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.create_record(*args, **kwargs)
        )

    @retry_timeout
    async def update_record(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.update_record(*args, **kwargs)
        )

    @retry_timeout
    async def patch_record(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.patch_record(*args, **kwargs))

    @retry_timeout
    async def delete_record(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_record(*args, **kwargs)
        )

    @retry_timeout
    async def delete_records(self, *args, **kwargs) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.delete_records(*args, **kwargs)
        )

    @retry_timeout
    async def get_history(self, *args, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_history(*args, **kwargs))

    @retry_timeout
    async def purge_history(self, *args, **kwargs) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._client.purge_history(*args, **kwargs)
        )

    @retry_timeout
    async def get_endpoint(self, *args, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._client.get_endpoint(*args, **kwargs))

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
