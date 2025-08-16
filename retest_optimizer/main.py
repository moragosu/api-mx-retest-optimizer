from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from retest_optimizer.db.redis_config import (
    close_redis_connection,
    connect_to_redis,
)
from retest_optimizer.routers import bulk_items_router, single_item_router
from retest_optimizer.utils.logging_config import setup_logging

# 로깅 설정
setup_logging()


# 애플리케이션의 시작과 종료 시점에 실행될 로직을 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션의 라이프사이클 동안 리소스를 관리합니다.
    - 시작 시: Redis에 연결합니다.
    - 종료 시: Redis 연결을 닫습니다.
    """
    logger.info("애플리케이션을 시작합니다...")
    await connect_to_redis()
    logger.info("Redis에 성공적으로 연결되었습니다.")

    yield  # 애플리케이션이 실행되는 동안 여기에서 대기합니다.

    logger.info("애플리케이션을 종료합니다...")
    await close_redis_connection()
    logger.info("Redis 연결이 성공적으로 종료되었습니다.")


# FastAPI 애플리케이션 인스턴스 생성 및 lifespan 설정
app = FastAPI(
    title="Manufacturing Inspection API",
    description="휴대폰 제조 공정 검사기용 RESTful API",
    version="1.0.0",
    lifespan=lifespan,
)

# 라우터 포함
app.include_router(single_item_router.router, tags=["Single Item Operations"])
app.include_router(bulk_items_router.router, tags=["Bulk Items Operations"])


@app.get("/", summary="Health Check", description="API 서버의 상태를 확인합니다.")
async def root():
    """기본적인 헬스 체크 엔드포인트입니다."""
    logger.info("Health check 요청 수신")
    return {"message": "Inspection API is running"}
