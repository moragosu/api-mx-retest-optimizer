from aredis_om import get_redis_connection
from loguru import logger

from ..config import settings
from ..models.defect_model import Defect

redis_conn = None


async def connect_to_redis():
    """Redis 연결을 생성하고 전역 변수에 할당합니다."""
    global redis_conn
    try:
        redis_conn = get_redis_connection(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        Defect.Meta.database = redis_conn
        await redis_conn.ping()
    except Exception as e:
        logger.error(f"Redis 연결에 실패했습니다: {e}")
        raise


async def close_redis_connection():
    """Redis 연결을 종료합니다."""
    global redis_conn
    if redis_conn:
        await redis_conn.close()


def get_redis_instance():
    """현재 활성화된 Redis 연결 인스턴스를 반환합니다."""
    if not redis_conn:
        raise ConnectionError(
            "Redis is not connected. The application might not have started correctly."
        )
    return redis_conn


def get_defect_key(pk: str) -> str:
    """
    Defect 모델의 네임스페이스와 주어진 PK를 조합하여 실제 Redis 키를 생성합니다.
    redis-om의 내부 키 생성 규칙을 따릅니다.
    """
    return f"{pk}"
