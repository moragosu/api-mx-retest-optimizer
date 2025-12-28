from aredis_om import Field as RedisField
from aredis_om import HashModel
from redis.asyncio.client import Redis


class RedisDefect(HashModel):
    factory_code: str = RedisField()
    process_code: str = RedisField()
    product_model: str = RedisField()
    defect_item: str = RedisField()
    analysis_period: int = RedisField()
    analysis_criteria: str = RedisField()
    reproducibility_rate: float = RedisField(default=0.0)
    total_inspections: int = RedisField(default=0)
    reproduced_count: int = RedisField(default=0)

    class Meta:
        database: Redis
