from dataclasses import dataclass
from typing import Iterable, List, Optional

from retest_optimizer.domain.entities.defect import (
    DefectRecord,
    generate_defect_pk,
)
from retest_optimizer.domain.repositories.defect_repository import DefectRepository


@dataclass
class InspectionResult:
    remove_retest: Optional[bool]
    reproducibility_rate: float
    alarm_history: str
    target_line: bool
    pk: Optional[str]


@dataclass
class DeleteResult:
    defect_item: str
    deleted_count: int
    error_messages: List[str]

    @property
    def error_count(self) -> int:
        return len(self.error_messages)


class InspectionService:
    def __init__(self, repository: DefectRepository):
        self._repository = repository

    async def check_defect(
        self,
        *,
        factory_code: str,
        process_code: str,
        product_model: str,
        defect_item: str,
        analysis_period: int,
        analysis_criteria: str,
        reproducibility_criteria: float,
        min_inspection_criteria: int,
        ip: str,
    ) -> InspectionResult:
        target_line = await self._is_target_ip(ip)
        if not target_line:
            return InspectionResult(
                remove_retest=None,
                reproducibility_rate=0.0,
                alarm_history="0/0",
                target_line=False,
                pk=None,
            )

        pk = generate_defect_pk(
            factory_code=factory_code,
            process_code=process_code,
            product_model=product_model,
            defect_item=defect_item,
            analysis_period=analysis_period,
            analysis_criteria=analysis_criteria,
        )
        record = await self._repository.get(pk)
        response_pk = f"{pk}:{ip}"

        if record is None:
            return InspectionResult(
                remove_retest=False,
                reproducibility_rate=0.0,
                alarm_history="0/0",
                target_line=True,
                pk=response_pk,
            )

        remove_retest = record.meets_thresholds(
            reproducibility_threshold=reproducibility_criteria,
            minimum_inspections=min_inspection_criteria,
        )
        return InspectionResult(
            remove_retest=remove_retest,
            reproducibility_rate=record.reproducibility_rate,
            alarm_history=record.alarm_history,
            target_line=True,
            pk=response_pk,
        )

    async def upsert_defect(self, defect: DefectRecord) -> str:
        await self._repository.save(defect)
        return defect.pk

    async def delete_defect_records(
        self,
        *,
        factory_code: str,
        process_code: str,
        product_model: str,
        defect_item: str,
        periods: Iterable[int],
        criteria: Iterable[str],
    ) -> DeleteResult:
        pks = [
            generate_defect_pk(
                factory_code=factory_code,
                process_code=process_code,
                product_model=product_model,
                defect_item=defect_item,
                analysis_period=period,
                analysis_criteria=criterion,
            )
            for period in periods
            for criterion in criteria
        ]

        deleted_count = 0
        error_messages: List[str] = []
        for pk in pks:
            try:
                deleted = await self._repository.delete(pk)
                if deleted:
                    deleted_count += 1
            except Exception as exc:  # pragma: no cover - logging responsibility of caller
                error_messages.append(f"Redis deletion failed for {pk}: {exc}")

        return DeleteResult(
            defect_item=defect_item,
            deleted_count=deleted_count,
            error_messages=error_messages,
        )

    async def _is_target_ip(self, ip: str) -> bool:
        # TODO: Implement target line filtering strategy
        return True
