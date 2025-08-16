import uvicorn

from retest_optimizer.config import settings


def main():
    """
    Uvicorn 서버를 실행하여 FastAPI 애플리케이션을 시작합니다.
    .env 파일 또는 환경 변수로부터 설정을 로드합니다.
    """
    uvicorn.run(
        "retest_optimizer.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
    )


if __name__ == "__main__":
    main()
