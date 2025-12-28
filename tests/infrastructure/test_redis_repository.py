import asyncio
import pytest

fakeredis = pytest.importorskip(
    "fakeredis.aioredis", reason="fakeredis is required for Redis repository tests"
)

from retest_optimizer.domain.entities.defect import DefectRecord, generate_defect_pk
from retest_optimizer.infrastructure.redis.defect_repository import RedisDefectRepository


class StubConnectionProvider:
    def __init__(self, client):
        self._client = client

    @property
    def client(self):  # pragma: no cover - simple data access
        return self._client


@pytest.fixture
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        asyncio.run(client.flushall())
        asyncio.run(client.close())


@pytest.fixture
def repository(fake_redis):
    provider = StubConnectionProvider(fake_redis)
    return RedisDefectRepository(provider)


def test_save_and_get_round_trip(repository):
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

    asyncio.run(repository.save(record))
    retrieved = asyncio.run(repository.get(record.pk))

    assert retrieved == record


def test_delete_returns_true_when_record_exists(repository):
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
    asyncio.run(repository.save(record))

    deleted = asyncio.run(repository.delete(record.pk))

    assert deleted is True
    assert asyncio.run(repository.get(record.pk)) is None


def test_delete_returns_false_when_record_missing(repository):
    pk = generate_defect_pk(
        factory_code="F1",
        process_code="P2",
        product_model="ModelX",
        defect_item="Scratch",
        analysis_period=7,
        analysis_criteria="WEEKLY",
    )

    deleted = asyncio.run(repository.delete(pk))

    assert deleted is False


def test_delete_many_counts_deleted_records(repository):
    records = [
        DefectRecord(
            factory_code="F1",
            process_code="P2",
            product_model="ModelX",
            defect_item="Scratch",
            analysis_period=period,
            analysis_criteria="WEEKLY",
            reproducibility_rate=0.9,
            total_inspections=150,
            reproduced_count=135,
        )
        for period in (7, 14)
    ]
    for record in records:
        asyncio.run(repository.save(record))

    deleted = asyncio.run(repository.delete_many([record.pk for record in records]))

    assert deleted == 2
    for record in records:
        assert asyncio.run(repository.get(record.pk)) is None
