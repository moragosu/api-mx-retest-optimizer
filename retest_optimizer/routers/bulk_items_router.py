import asyncio
from typing import List

from fastapi import APIRouter, Body, status
from loguru import logger

from ..services.redis_operations import check_defect_item, create_or_update_defect_record, delete_defect_record
from ..models.defect_model import (
    BulkCreateRecordRequest,
    BulkInspectionRequest,
    BulkInspectionResponse,
    BulkDeleteRecordRequest,
    CreateRecordRequest,
    CreateResponse,
    DeleteRecordRequest,
    DeleteResponse,
    InspectionRequest,
    InspectionResponse,
)

router = APIRouter(prefix="/api/v1/inspection/bulk")


async def process_single_check_request(
    request: InspectionRequest,
) -> InspectionResponse:
    """단일 조회 요청을 처리하는 내부 헬퍼 함수"""
    try:
        result = await check_defect_item(request)
        return InspectionResponse(
            retest_needed=result["retest_needed"],
            reproducibility_rate=result["reproducibility_rate"],
            alarm_history=result["alarm_history"],
            request_data=request
        )
    except Exception as e:
        logger.error(f"벌크 조회 중 개별 항목 에러: {e}")
        return InspectionResponse(
            retest_needed=False,
            reproducibility_rate=0.0,
            alarm_history="error",
            request_data=request,
        )


@router.post(
    "/check",
    response_model=BulkInspectionResponse,
    summary="여러 불량 항목 재검사 여부 동시 조회",
)
async def check_bulk_items(bulk_request: BulkInspectionRequest = Body(...)):
    logger.info(f"벌크 조회 요청 수신: {len(bulk_request.requests)}개 항목")
    tasks = [process_single_check_request(req) for req in bulk_request.requests]
    results = await asyncio.gather(*tasks)
    logger.success(f"벌크 조회 처리 완료: {len(results)}개 항목")
    return BulkInspectionResponse(results=results)


async def process_single_create_record(record: CreateRecordRequest) -> CreateResponse:
    """단일 레코드 저장을 처리하는 내부 헬퍼 함수"""
    try:
        result = await create_or_update_defect_record(record)
        return CreateResponse(pk=result["pk"], status=result["status"])
    except Exception as e:
        logger.error(f"벌크 저장 중 개별 항목 에러: {e}")
        return CreateResponse(pk="error", status=f"error: {e}")


@router.post(
    "/records",
    response_model=List[CreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="여러 불량 데이터 동시 생성/업데이트",
)
async def create_or_update_bulk_records(
    bulk_record: BulkCreateRecordRequest = Body(...),
):
    logger.info(f"벌크 레코드 생성/업데이트 요청: {len(bulk_record.records)}개 항목")
    tasks = [process_single_create_record(rec) for rec in bulk_record.records]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if "error" not in r.status)
    logger.success(f"벌크 레코드 처리 완료. 성공: {success_count}/{len(results)}")
    return results


async def process_single_delete_request(
    request: DeleteRecordRequest,
) -> DeleteResponse:
    """단일 삭제 요청을 처리하는 내부 헬퍼 함수"""
    try:
        result = await delete_defect_record(request)
        return DeleteResponse(
            defect_item=result["defect_item"],
            deleted_count=result["deleted_count"],
            error_count=result["error_count"],
            error_messages=result["error_messages"]
        )
    except Exception as e:
        logger.error(f"벌크 삭제 중 개별 항목 에러: {e}")
        return DeleteResponse(
            defect_item=request.defect_item,
            deleted_count=0,
            error_count=1,
            error_messages=[f"error: {e}"]
        )


@router.delete(
    "/records",
    response_model=List[DeleteResponse],
    summary="여러 불량 데이터 동시 삭제",
)
async def delete_bulk_records(
    bulk_delete: BulkDeleteRecordRequest = Body(...),
):
    logger.info(f"벌크 레코드 삭제 요청: {len(bulk_delete.requests)}개 항목")
    tasks = [process_single_delete_request(req) for req in bulk_delete.requests]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if r.error_count == 0)
    logger.success(f"벌크 삭제 처리 완료. 성공: {success_count}/{len(results)}")
    return results
