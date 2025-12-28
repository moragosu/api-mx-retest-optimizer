import asyncio
import pytest

from retest_optimizer.application.inspection_service import InspectionResult, InspectionService
from retest_optimizer.domain.entities.defect import DefectRecord, generate_defect_pk


class InMemoryDefectRepository:
    def __init__(self):
        self.storage: dict[str, DefectRecord] = {}
        self.delete_behavior: dict[str, Exception | bool] = {}

    async def get(self, pk: str) -> DefectRecord | None:
        return self.storage.get(pk)

    async def save(self, defect: DefectRecord) -> None:
        self.storage[defect.pk] = defect

    async def delete(self, pk: str) -> bool:
        behavior = self.delete_behavior.get(pk)
        if isinstance(behavior, Exception):
            raise behavior
        if behavior is False:
            return False
        removed = self.storage.pop(pk, None)
        return removed is not None

    async def delete_many(self, pks):
        deleted = 0
        for pk in pks:
            if await self.delete(pk):
                deleted += 1
        return deleted


class StubInspectionService(InspectionService):
    def __init__(self, repository: InMemoryDefectRepository, *, is_target: bool = True):
        super().__init__(repository)
        self._is_target = is_target

    async def _is_target_ip(self, ip: str) -> bool:  # pragma: no cover - used in tests
        return self._is_target


@pytest.fixture
def repository() -> InMemoryDefectRepository:
    return InMemoryDefectRepository()


@pytest.fixture
def service(repository: InMemoryDefectRepository) -> InspectionService:
    return StubInspectionService(repository)


def test_check_defect_returns_non_target_line_when_ip_filtered(
    repository: InMemoryDefectRepository,
) -> None:
    service = StubInspectionService(repository, is_target=False)

    result = asyncio.run(
        service.check_defect(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
        reproducibility_criteria=0.5,
        min_inspection_criteria=100,
        ip="10.0.0.1",
        )
    )

    assert result == InspectionResult(
        remove_retest=None,
        reproducibility_rate=0.0,
        alarm_history="0/0",
        target_line=False,
        pk=None,
    )


def test_check_defect_returns_defaults_when_record_missing(
    service: InspectionService,
) -> None:
    result = asyncio.run(
        service.check_defect(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
        reproducibility_criteria=0.5,
        min_inspection_criteria=100,
        ip="10.0.0.1",
        )
    )

    assert result.remove_retest is False
    assert result.reproducibility_rate == 0.0
    assert result.alarm_history == "0/0"
    assert result.target_line is True
    assert result.pk == "7:WEEKLY:F1:P2:ModelX:Scratch:10.0.0.1"


def test_check_defect_evaluates_thresholds_from_repository(
    repository: InMemoryDefectRepository,
) -> None:
    record = DefectRecord(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
        reproducibility_rate=0.9,
        total_inspections=150,
        reproduced_count=135,
    )
    async def scenario() -> InspectionResult:
        await repository.save(record)
        service = StubInspectionService(repository)
        return await service.check_defect(
            factory_code="F1",
            process_code="P2",
            product_model="ModelX",
            defect_item="Scratch",
            analysis_period=7,
            analysis_criteria="WEEKLY",
            reproducibility_criteria=0.8,
            min_inspection_criteria=120,
            ip="10.0.0.1",
        )

    result = asyncio.run(scenario())

    assert result.remove_retest is True
    assert result.reproducibility_rate == pytest.approx(0.9)
    assert result.alarm_history == "135/150"
    assert result.target_line is True


def test_upsert_defect_saves_record(repository: InMemoryDefectRepository) -> None:
    service = StubInspectionService(repository)
    record = DefectRecord(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
        reproducibility_rate=0.9,
        total_inspections=150,
        reproduced_count=135,
    )

    pk = asyncio.run(service.upsert_defect(record))

    assert pk == record.pk
    assert repository.storage[pk] == record


def test_delete_defect_records_counts_deletions_and_errors(
    repository: InMemoryDefectRepository,
) -> None:
    pk_success = generate_defect_pk(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
    )
    pk_error = generate_defect_pk(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=14,
        analysis_criteria="WEEKLY",
    )

    repository.storage[pk_success] = DefectRecord(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
        reproducibility_rate=0.6,
        total_inspections=80,
        reproduced_count=48,
    )
    repository.delete_behavior[pk_error] = RuntimeError("boom")

    service = StubInspectionService(repository)

    result = asyncio.run(
        service.delete_defect_records(
            factory_code="F1",
            process_code="P2",
            product_model="ModelX",
            defect_item="Scratch",
            periods=[7, 14],
            criteria=["WEEKLY"],
        )
    )

    assert result.deleted_count == 1
    assert result.error_count == 1
    assert pk_error in result.error_messages[0]
    assert result.defect_item == "Scratch"
