from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ValidationUtils:
    @staticmethod
    def validate_analysis_period(value: int) -> int:
        if value not in {2, 4, 6}:
            raise ValueError("분석 기간은 2, 4, 6주만 가능합니다")
        return value

    @staticmethod
    def validate_analysis_criteria(value: str) -> str:
        if value.lower() not in {"retest", "retry"}:
            raise ValueError("분석 기준은 retest 또는 retry만 가능합니다")
        return value


class InspectionRequest(BaseModel):
    factory_code: str = Field(..., description="공장 코드", example="SEV")
    analysis_criteria: str = Field(..., description="분석 기준", example="retest")
    ip: str = Field(..., description="IP 주소", example="10.56.123.125")
    process_code: str = Field(..., description="테스트 공정 코드", example="TOP41")
    product_model: str = Field(..., description="제품 모델", example="SM-S938U")
    min_inspection_criteria: int = Field(..., description="최소 검사 기준", example=5)
    reproducibility_criteria: float = Field(..., description="재현률 기준", example=0.98)
    analysis_period: int = Field(..., description="분석 기간 (주 단위)", example=4)
    defect_item: str = Field(..., description="불량 항목", example="NX_RX_SURAD")

    _validate_analysis_period = field_validator("analysis_period")(ValidationUtils.validate_analysis_period)
    _validate_analysis_criteria = field_validator("analysis_criteria")(ValidationUtils.validate_analysis_criteria)


class BulkInspectionRequest(BaseModel):
    requests: List[InspectionRequest]


class InspectionResponse(BaseModel):
    remove_retest: Optional[bool] = Field(..., description="재검사 제거 여부")
    reproducibility_rate: float = Field(..., description="조회된 재현률", example=0.98)
    alarm_history: str = Field(..., description="알람 이력", example="98/100")
    target_line: bool = Field(..., description="대상 라인 여부", example=True)
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

    _validate_analysis_period = field_validator("analysis_period")(ValidationUtils.validate_analysis_period)
    _validate_analysis_criteria = field_validator("analysis_criteria")(ValidationUtils.validate_analysis_criteria)


class BulkCreateRecordRequest(BaseModel):
    records: List[CreateRecordRequest]


class CreateResponse(BaseModel):
    pk: str
    status: str


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
