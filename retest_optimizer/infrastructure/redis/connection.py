from typing import Optional

from aredis_om import get_redis_connection
from redis.asyncio.client import Redis

from retest_optimizer.config import settings


class RedisConnectionProvider:
    def __init__(self) -> None:
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        if self._client is None:
            self._client = get_redis_connection(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            await self._client.ping()

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise ConnectionError(
                "Redis connection has not been established. Ensure connect() was awaited."
            )
        return self._client
