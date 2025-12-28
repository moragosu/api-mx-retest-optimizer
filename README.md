# 프로세스 최적화를 위한 RESTful API

## 1. 프로젝트 개요
이 프로젝트는 특정 프로세스에서 재평가가 필요한 항목을 판단하기 위한 RESTful API 서버입니다. 재발생 확률이 높은 항목을 식별함으로써, 불필요한 검사를 건너뛰고 즉각적인 결정을 내릴 수 있어 생산성을 향상시킵니다.

## 2. 주요 기능
- **실시간 의사 결정**: 항목 데이터를 받아 머신러닝 또는 통계 배치 시스템에서 미리 계산된 확률 데이터를 기반으로 재평가 필요 여부를 결정합니다.
- **단일 및 대량 처리**: 단일 항목과 다중 항목(대량) 처리 모두를 지원하는 전용 API를 제공하여 네트워크 효율성을 높입니다.
- **데이터 입출력**:
    - **출력 (Check)**: 항목의 평가 상태를 조회하기 위한 엔드포인트(`/check`) 제공
    - **입력 (Record)**: 배치 시스템이 계산된 확률 데이터를 Redis에 저장 및 업데이트하기 위한 엔드포인트(`/record`) 제공

## 3. 기술 스택
- **웹 프레임워크**: FastAPI (비동기 처리, 고성능, 자동 API 문서화)
- **데이터베이스**: Redis (인메모리 데이터베이스로 빠른 응답 보장)
- **로깅**: Loguru (간결한 로깅 설정)
- **설정 관리**: Pydantic-Settings (환경 변수와 .env 파일을 통한 안전한 설정 관리)
- **서버**: Uvicorn (ASGI 서버)

## 4. 프로젝트 구조
```
.
├── logs/                     # 로그 파일 저장 디렉토리
├── .env.dev                  # 개발 환경 설정 파일
├── .env.{loation}            # 운영 환경 설정 파일 (위치별) 예:.env.gumi
├── pyproject.toml            # 프로젝트 설정 및 의존성 관리 파일
├── config.py                 # Pydantic-Settings를 사용한 환경 변수 관리
├── main.py                   # FastAPI 애플리케이션 메인 진입점 (lifespan, router 포함)
├── domain
│   ├── entities
│   │   └── defect.py         # 핵심 도메인 엔티티 및 키 생성 로직
│   └── repositories
│       └── defect_repository.py # 도메인 리포지토리 인터페이스 정의
├── application
│   └── inspection_service.py # 비즈니스 규칙을 구현한 서비스 계층
├── infrastructure
│   └── redis
│       ├── connection.py     # Redis 연결 수명주기 관리
│       └── defect_repository.py # Redis 기반 리포지토리 구현체
├── routers
│   ├── schemas.py            # API 전용 요청/응답 모델
│   ├── single_item_router.py # 단일 항목 처리 API 라우터
│   └── bulk_items_router.py  # 대량 항목 처리 API 라우터
└── utils
    └── logging_config.py     # Loguru 로깅 설정
```

## 5. 설치 및 설정

### 1. 필수 조건
- Python 3.10+
- 실행 중인 Redis 서버

### 2. 의존성 설치
이 프로젝트는 `uv`를 사용하여 의존성을 관리합니다. `uv`는 매우 빠른 Python 패키지 설치 도구입니다.

#### uv 설치
`uv`가 설치되어 있지 않다면, 터미널에서 다음 명령 중 하나를 실행하세요. 자세한 내용은 [공식 설치 가이드](https://docs.astral.sh/uv/getting-started/installation/)를 참조하세요.
```
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
irm https://astral.sh/uv/install.ps1 | iex
```

#### 의존성 동기화
프로젝트 루트 디렉토리에서 다음 명령을 실행하세요. 이 명령은 `pyproject.toml` 파일을 읽고 필요한 모든 라이브러리를 가상 환경에 설치합니다.
```
uv sync --native-tls
```

### 3. 환경 변수 설정
`.env.dev`(개발), `.env.{location}`(운영) 로컬 환경에 맞게 업데이트하세요.

예:
```
# .env 파일
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<PASSWORD>
```

### 4. API 서버 실행
서버를 두 가지 방법으로 실행할 수 있습니다:

1. **Uvicorn으로 직접 실행 (개발용 권장):**
    이 방법은 개발에 권장됩니다. `--reload` 플래그와 같은 서버 설정을 직접 제어할 수 있어 코드 변경 시 서버가 자동으로 재시작됩니다.

    ```bash
    uvicorn retest_optimizer.main:app --host 0.0.0.0 --port 8000 --reload
    ```

2. **Python 모듈로 실행:**
    Python 모듈로 프로젝트를 실행할 수도 있습니다. 이 명령은 더 깔끔하지만 포트나 재시작 모드와 같은 서버 설정은 `retest_optimizer/__main__.py` 파일 내에서 구성됩니다.

    ```bash
    python -m retest_optimizer
    ``` 
    or
    ```bash
    uv run -m retest_optimizer
    ```
### 5. API 문서 및 테스트
서버가 실행 중일 때, 웹 브라우저에서 자동 생성된 API 문서에 접근하여 엔드포인트를 탐색하고 테스트할 수 있습니다.
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### 6. 테스트 실행 방법
이 프로젝트의 테스트 스위트는 **도메인 → 애플리케이션 → 인프라** 순으로 레이어를 따라가며 작성되어 있습니다. 테스트를 실행하기 전에 아래 순서를 참고하세요.

#### 6.1 테스트 의존성 준비
1. 개발용 가상환경을 초기화했다면 한 번만 다음 명령으로 테스트 도구를 설치합니다.
   ```bash
   uv sync --dev --native-tls
   ```
2. Redis 통합 테스트를 로컬에서 실행하려면 선택적으로 `fakeredis`를 추가합니다. (설치하지 않으면 해당 테스트는 자동으로 건너뜁니다.)
   ```bash
   uv pip install "fakeredis[asyncio]"
   ```

#### 6.2 전체 테스트 실행
모든 계층의 테스트를 한 번에 실행하려면 프로젝트 루트에서 다음 명령을 실행합니다.

```bash
uv run pytest
```

#### 6.3 계층별 실행
필요에 따라 관심 있는 계층만 선택적으로 실행할 수 있습니다.

```bash
# 도메인 규칙 검증
uv run pytest tests/domain

# 애플리케이션 서비스(유즈케이스) 검증
uv run pytest tests/application

# Redis 인프라 통합 테스트
uv run pytest tests/infrastructure
```

> **참고:** `tests/infrastructure`는 `fakeredis`가 설치되어 있거나 별도의 Redis 테스트 인스턴스를 띄워 둔 환경에서만 정상적으로 동작합니다. 설치되어 있지 않으면 `pytest`가 해당 테스트를 건너뜁니다.
