from fastapi import Request

from retest_optimizer.application.inspection_service import InspectionService
from retest_optimizer.infrastructure.redis.connection import RedisConnectionProvider
from retest_optimizer.infrastructure.redis.defect_repository import RedisDefectRepository


def get_inspection_service(request: Request) -> InspectionService:
    connection_provider: RedisConnectionProvider = request.app.state.redis_provider
    repository = RedisDefectRepository(connection_provider)
    return InspectionService(repository)
