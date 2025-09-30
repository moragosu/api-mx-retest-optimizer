from typing import Iterable, Optional, Protocol

from retest_optimizer.domain.entities.defect import DefectRecord


class DefectRepository(Protocol):
    async def get(self, pk: str) -> Optional[DefectRecord]:
        ...

    async def save(self, defect: DefectRecord) -> None:
        ...

    async def delete(self, pk: str) -> bool:
        ...

    async def delete_many(self, pks: Iterable[str]) -> int:
        ...
