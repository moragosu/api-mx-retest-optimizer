from typing import List
from pydantic import field_validator
from aredis_om import Field as RedisField
from aredis_om import HashModel
from pydantic import BaseModel, Field
from redis.asyncio.client import Redis

# 유틸리티 클래스: 유효성 검사 함수 모음
class ValidationUtils:
    @staticmethod
    def validate_analysis_period(v):
        if v not in [2, 4, 6]:
            raise ValueError("분석 기간은 2, 4, 6주만 가능합니다")
        return v

    @staticmethod
    def validate_analysis_criteria(v):
        if v.lower() not in ["retest", "retry"]:
            raise ValueError("분석 기준은 retest 또는 retry만 가능합니다")
        return v


class Defect(HashModel):
    """
    Redis에 저장될 불량 데이터의 스키마를 정의합니다. (직접 인스턴스화하여 사용하지는 않음)
    HashModel을 상속받아 Redis-OM과 호환되는 키 네임스페이스를 유지합니다.
    """

    factory_code: str = RedisField(description="공장 코드 (예: SEV)")
    process_code: str = RedisField(description="테스트 공정 코드 (예: TOP41)")
    product_model: str = RedisField(description="제품 모델 (예: SM-S938U)")
    defect_item: str = RedisField(description="불량 항목 (예: NX_RX_SURAD)")
    reproducibility_rate: float = RedisField(
        default=0.0, description="재현률 (0.0 ~ 1.0)"
    )
    total_inspections: int = RedisField(default=0, description="총 검사 횟수")
    reproduced_count: int = RedisField(default=0, description="재현된 횟수")

    class Meta:
        database: Redis


# API 요청 모델
class InspectionRequest(BaseModel):
    """검사기로부터 받는 요청 데이터 모델입니다."""

    factory_code: str = Field(..., description="공장 코드", example="SEV")
    analysis_criteria: str = Field(..., description="분석 기준", example="retest")
    process_code: str = Field(..., description="테스트 공정 코드", example="TOP41")
    product_model: str = Field(..., description="제품 모델", example="SM-S938U")
    min_inspection_criteria: int = Field(..., description="최소 검사 기준", example=5)
    reproducibility_criteria: float = Field(..., description="재현률 기준", example=0.98)
    analysis_period: int = Field(..., description="분석 기간 (주 단위)", example=4)
    defect_item: str = Field(..., description="불량 항목", example="NX_RX_SURAD")

    _validate_analysis_period = field_validator('analysis_period')(ValidationUtils.validate_analysis_period)
    _validate_analysis_criteria = field_validator('analysis_criteria')(ValidationUtils.validate_analysis_criteria)


class BulkInspectionRequest(BaseModel):
    requests: List[InspectionRequest]


# API 응답 모델
class InspectionResponse(BaseModel):
    retest_needed: bool = Field(
        ..., description="재검사 필요 여부 (true: 재검사 불필요, false: 재검사 필요)"
    )
    reproducibility_rate: float = Field(..., description="조회된 재현률", example=0.98)
    alarm_history: str = Field(
        ..., description="알람 이력 (재현된 횟수/총 검사 횟수)", example="98/100"
    )
    request_data: InspectionRequest


class BulkInspectionResponse(BaseModel):
    results: List[InspectionResponse]


class CreateRecordRequest(BaseModel):
    factory_code: str = Field(..., description="공장 코드", example="SEV")
    process_code: str = Field(..., description="테스트 공정 코드", example="TOP41")
    product_model: str = Field(..., description="제품 모델", example="SM-S938U")
    defect_item: str = Field(..., description="불량 항목", example="NX_RX_SURAD")
    reproducibility_rate: float = Field(..., description="재현률", example=0.98)
    total_inspections: int = Field(..., description="총 검사 횟수", example=100)
    reproduced_count: int = Field(..., description="재현된 횟수", example=98)
    analysis_criteria: str = Field(..., description="분석 기준", example="retest")
    analysis_period: int = Field(..., description="분석 기간 (주 단위)", example=4)

    _validate_analysis_period = field_validator('analysis_period')(ValidationUtils.validate_analysis_period)
    _validate_analysis_criteria = field_validator('analysis_criteria')(ValidationUtils.validate_analysis_criteria)


class BulkCreateRecordRequest(BaseModel):
    records: List[CreateRecordRequest]


class DeleteRecordRequest(BaseModel):
    factory_code: str = Field(..., description="공장 코드", example="SEV")
    process_code: str = Field(..., description="테스트 공정 코드", example="TOP41")
    product_model: str = Field(..., description="제품 모델", example="SM-S938U")
    defect_item: str = Field(..., description="불량 항목", example="NX_RX_SURAD")


class BulkDeleteRecordRequest(BaseModel):
    requests: List[DeleteRecordRequest]


class DeleteResponse(BaseModel):
    defect_item: str = Field(..., description="삭제 대상 불량 항목")
    deleted_count: int = Field(..., description="성공적으로 삭제된 레코드 수")
    error_count: int = Field(..., description="삭제 실패 횟수")
    error_messages: List[str] = Field(default_factory=list, description="에러 메시지 목록")


class CreateResponse(BaseModel):
    pk: str
    status: str
