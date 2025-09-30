from fastapi import APIRouter, Body, HTTPException, status
from loguru import logger

from ..services.redis_operations import check_defect_item, create_or_update_defect_record, delete_defect_record
from ..models.defect_model import (
    CreateRecordRequest,
    CreateResponse,
    DeleteRecordRequest,
    DeleteResponse,
    InspectionRequest,
    InspectionResponse,
)

router = APIRouter(prefix="/api/v1/inspection/single")


@router.post(
    "/check",
    response_model=InspectionResponse,
    summary="단일 불량 항목 재검사 여부 조회",
    description="주어진 조건에 따라 특정 불량 항목의 재검사 필요 여부를 판단하여 반환합니다.",
)
async def check_single_item(request: InspectionRequest = Body(...)):
    logger.info(f"단일 항목 조회 요청 수신: {request.model_dump()}")

    try:
        result = await check_defect_item(request)
        response = InspectionResponse(
            remove_retest=result["remove_retest"],
            reproducibility_rate=result["reproducibility_rate"],
            alarm_history=result["alarm_history"],
            target_line=result["target_line"],
            request_data=request
        )
        logger.info(f"단일 항목 조회 응답: {response.model_dump()}")
        return response
    except Exception as e:
        logger.error(f"Redis 조회 중 에러 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


@router.post(
    "/record",
    response_model=CreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="단일 불량 데이터 생성/업데이트",
    description="커스텀 PK를 사용하여 불량 데이터를 Redis에 저장(생성 또는 덮어쓰기)합니다.",
)
async def create_or_update_record(record: CreateRecordRequest = Body(...)):
    logger.info(f"단일 레코드 생성/업데이트 요청: {record.model_dump()}")

    try:
        result = await create_or_update_defect_record(record)
        logger.success(f"레코드 저장 완료. PK: {result['pk']}")
        response = CreateResponse(pk=result["pk"], status=result["status"])
        logger.info(f"단일 레코드 생성/업데이트 응답: {response.model_dump()}")
        return response
    except Exception as e:
        logger.error(f"레코드 저장 중 에러 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )


@router.delete(
    "/record",
    response_model=DeleteResponse,
    summary="단일 불량 데이터 삭제",
    description="주어진 불량 항목에 대해 2,4,6주/retry,retest 모든 조합의 데이터를 삭제합니다.",
)
async def delete_record(request: DeleteRecordRequest = Body(...)):
    logger.info(f"단일 레코드 삭제 요청: {request.model_dump()}")

    try:
        result = await delete_defect_record(request)
        logger.success(f"레코드 삭제 완료. 삭제된 레코드 수: {result['deleted_count']}")
        response = DeleteResponse(
            defect_item=result["defect_item"],
            deleted_count=result["deleted_count"],
            error_count=result["error_count"],
            error_messages=result["error_messages"]
        )
        logger.info(f"단일 레코드 삭제 응답: {response.model_dump()}")
        return response
    except Exception as e:
        logger.error(f"레코드 삭제 중 에러 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다.",
        )
