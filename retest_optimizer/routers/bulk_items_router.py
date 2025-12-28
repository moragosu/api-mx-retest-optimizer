import asyncio
from typing import List

from fastapi import APIRouter, Body, Depends, status
from loguru import logger

from retest_optimizer.application.inspection_service import InspectionService
from retest_optimizer.domain.entities.defect import DefectRecord
from retest_optimizer.routers.dependencies import get_inspection_service
from retest_optimizer.routers.schemas import (
    BulkCreateRecordRequest,
    BulkDeleteRecordRequest,
    BulkInspectionRequest,
    BulkInspectionResponse,
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
    service: InspectionService,
) -> InspectionResponse:
    """단일 조회 요청을 처리하는 내부 헬퍼 함수"""
    try:
        result = await service.check_defect(
            factory_code=request.factory_code,
            process_code=request.process_code,
            product_model=request.product_model,
            defect_item=request.defect_item,
            analysis_period=request.analysis_period,
            analysis_criteria=request.analysis_criteria,
            reproducibility_criteria=request.reproducibility_criteria,
            min_inspection_criteria=request.min_inspection_criteria,
            ip=request.ip,
        )
        return InspectionResponse(
            remove_retest=result.remove_retest,
            reproducibility_rate=result.reproducibility_rate,
            alarm_history=result.alarm_history,
            target_line=result.target_line,
            request_data=request
        )
    except Exception as e:
        logger.error(f"벌크 조회 중 개별 항목 에러: {e}")
        return InspectionResponse(
            remove_retest=False,
            reproducibility_rate=0.0,
            alarm_history="error",
            target_line=False,
            request_data=request,
        )


@router.post(
    "/check",
    response_model=BulkInspectionResponse,
    summary="여러 불량 항목 재검사 여부 동시 조회",
)
async def check_bulk_items(
    bulk_request: BulkInspectionRequest = Body(...),
    service: InspectionService = Depends(get_inspection_service),
):
    logger.info(f"벌크 조회 요청 수신: {len(bulk_request.requests)}개 항목")
    tasks = [process_single_check_request(req, service) for req in bulk_request.requests]
    results = await asyncio.gather(*tasks)
    logger.success(f"벌크 조회 처리 완료: {len(results)}개 항목")
    response = BulkInspectionResponse(results=results)
    logger.info(f"벌크 조회 응답: {response.model_dump()}")
    return response


async def process_single_create_record(
    record: CreateRecordRequest,
    service: InspectionService,
) -> CreateResponse:
    """단일 레코드 저장을 처리하는 내부 헬퍼 함수"""
    try:
        pk = await service.upsert_defect(
            DefectRecord(
                factory_code=record.factory_code,
                process_code=record.process_code,
                product_model=record.product_model,
                defect_item=record.defect_item,
                analysis_period=record.analysis_period,
                analysis_criteria=record.analysis_criteria,
                reproducibility_rate=record.reproducibility_rate,
                total_inspections=record.total_inspections,
                reproduced_count=record.reproduced_count,
            )
        )
        return CreateResponse(pk=pk, status="created_or_updated")
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
    service: InspectionService = Depends(get_inspection_service),
):
    logger.info(f"벌크 레코드 생성/업데이트 요청: {len(bulk_record.records)}개 항목")
    tasks = [process_single_create_record(rec, service) for rec in bulk_record.records]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if "error" not in r.status)
    logger.success(f"벌크 레코드 처리 완료. 성공: {success_count}/{len(results)}")
    logger.info(f"벌크 레코드 생성/업데이트 응답: {results}")
    return results


async def process_single_delete_request(
    request: DeleteRecordRequest,
    service: InspectionService,
) -> DeleteResponse:
    """단일 삭제 요청을 처리하는 내부 헬퍼 함수"""
    try:
        result = await service.delete_defect_records(
            factory_code=request.factory_code,
            process_code=request.process_code,
            product_model=request.product_model,
            defect_item=request.defect_item,
            periods=[2, 4, 6],
            criteria=["retry", "retest"],
        )
        return DeleteResponse(
            defect_item=result.defect_item,
            deleted_count=result.deleted_count,
            error_count=result.error_count,
            error_messages=result.error_messages
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
    service: InspectionService = Depends(get_inspection_service),
):
    logger.info(f"벌크 레코드 삭제 요청: {len(bulk_delete.requests)}개 항목")
    tasks = [process_single_delete_request(req, service) for req in bulk_delete.requests]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for r in results if r.error_count == 0)
    logger.success(f"벌크 삭제 처리 완료. 성공: {success_count}/{len(results)}")
    logger.info(f"벌크 레코드 삭제 응답: {results}")
    return results
