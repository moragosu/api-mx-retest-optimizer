from typing import Iterable, Optional

from redis.asyncio.client import Redis

from retest_optimizer.domain.entities.defect import DefectRecord
from retest_optimizer.domain.repositories.defect_repository import DefectRepository
from retest_optimizer.infrastructure.redis.connection import RedisConnectionProvider


class RedisDefectRepository(DefectRepository):
    def __init__(self, connection_provider: RedisConnectionProvider):
        self._connection_provider = connection_provider

    @property
    def _client(self) -> Redis:
        return self._connection_provider.client

    async def get(self, pk: str) -> Optional[DefectRecord]:
        data = await self._client.hgetall(pk)
        if not data:
            return None
        return self._deserialize(data)

    async def save(self, defect: DefectRecord) -> None:
        await self._client.hset(defect.pk, mapping=self._serialize(defect))

    async def delete(self, pk: str) -> bool:
        deleted = await self._client.delete(pk)
        return bool(deleted)

    async def delete_many(self, pks: Iterable[str]) -> int:
        deleted_total = 0
        for pk in pks:
            deleted = await self._client.delete(pk)
            deleted_total += int(bool(deleted))
        return deleted_total

    def _serialize(self, defect: DefectRecord) -> dict:
        return {
            "factory_code": defect.factory_code,
            "process_code": defect.process_code,
            "product_model": defect.product_model,
            "defect_item": defect.defect_item,
            "analysis_period": defect.analysis_period,
            "analysis_criteria": defect.analysis_criteria,
            "reproducibility_rate": defect.reproducibility_rate,
            "total_inspections": defect.total_inspections,
            "reproduced_count": defect.reproduced_count,
        }

    def _deserialize(self, data: dict) -> DefectRecord:
        return DefectRecord(
            factory_code=data["factory_code"],
            process_code=data["process_code"],
            product_model=data["product_model"],
            defect_item=data["defect_item"],
            analysis_period=int(data["analysis_period"]),
            analysis_criteria=data["analysis_criteria"],
            reproducibility_rate=float(data["reproducibility_rate"]),
            total_inspections=int(data["total_inspections"]),
            reproduced_count=int(data["reproduced_count"]),
        )
