from typing import Optional, Dict, Any
from loguru import logger
from redis.asyncio.client import Redis

from ..db.redis_config import get_defect_key, get_redis_instance
from ..models.defect_model import InspectionRequest, CreateRecordRequest, DeleteRecordRequest


async def generate_defect_pk(
    factory_code: str,
    process_code: str,
    product_model: str,
    defect_item: str,
    analysis_period: int,
    analysis_criteria: str
) -> str:
    """커스텀 PK 생성 함수"""
    return f"{analysis_period}:{analysis_criteria}:{factory_code}:{process_code}:{product_model}:{defect_item}"


async def is_target_ip(ip: str) -> bool:
    """IP가 대상 IP인지 확인하는 함수"""
    # TODO: 실제 대상 IP 목록 관리 방식에 따라 구현 필요
    return True


async def check_defect_item(request: InspectionRequest) -> Dict[str, Any]:
    """불량 항목 조회 및 재검사 필요 여부 판단"""
    # IP 기반 필터링
    target_line = await is_target_ip(request.ip)
    
    # 비대상 IP인 경우 None 응답 처리
    if not target_line:
        return {
            "remove_retest": None,
            "reproducibility_rate": 0.0,
            "alarm_history": "0/0",
            "target_line": False
        }

    custom_pk = await generate_defect_pk(
        request.factory_code,
        request.process_code,
        request.product_model,
        request.defect_item,
        request.analysis_period,
        request.analysis_criteria
    )
    
    # 응답에 IP를 포함한 PK 생성 (Redis 키로는 사용하지 않음)
    response_pk = f"{custom_pk}:{request.ip}"
    
    key_name = get_defect_key(custom_pk)
    redis = get_redis_instance()

    try:
        data = await redis.hgetall(key_name)
        if not data:
            return {
                "remove_retest": False,
                "reproducibility_rate": 0.0,
                "alarm_history": "0/0",
                "target_line": True,
                "pk": response_pk
            }

        reproducibility_rate = float(data["reproducibility_rate"])
        total_inspections = int(data["total_inspections"])
        reproduced_count = int(data["reproduced_count"])

        is_reproducible_enough = reproducibility_rate >= request.reproducibility_criteria
        has_enough_data = total_inspections >= request.min_inspection_criteria
        remove_retest = is_reproducible_enough and has_enough_data

        return {
            "remove_retest": remove_retest,
            "reproducibility_rate": reproducibility_rate,
            "alarm_history": f"{reproduced_count}/{total_inspections} ",
            "target_line": True,
            "pk": response_pk
        }

    except Exception as e:
        logger.error(f"Redis 조회 중 에러 발생 (PK: {custom_pk}): {e}")
        raise


async def create_or_update_defect_record(record: CreateRecordRequest) -> Dict[str, Any]:
    """불량 데이터 생성/업데이트"""
    custom_pk = await generate_defect_pk(
        record.factory_code,
        record.process_code,
        record.product_model,
        record.defect_item,
        record.analysis_period,
        record.analysis_criteria
    )
    key_name = get_defect_key(custom_pk)
    redis = get_redis_instance()

    try:
        await redis.hset(key_name, mapping=record.model_dump())
        return {"pk": custom_pk, "status": "created_or_updated"}
    except Exception as e:
        logger.error(f"Redis 저장 중 에러 발생 (PK: {custom_pk}): {e}")
        return {"pk": custom_pk, "status": f"error: {e}"}


async def delete_defect_record(request: DeleteRecordRequest) -> Dict[str, Any]:
    """불량 데이터 삭제 (2,4,6주 / retry,retest 모든 조합 삭제)"""
    redis = get_redis_instance()
    deleted_count = 0
    error_count = 0
    error_messages = []

    # 모든 분석 기간(2,4,6주)과 분석 기준(retry,retest) 조합에 대해 삭제 시도
    for period in [2, 4, 6]:
        for criteria in ["retry", "retest"]:
            try:
                custom_pk = await generate_defect_pk(
                    request.factory_code,
                    request.process_code,
                    request.product_model,
                    request.defect_item,
                    period,
                    criteria
                )
                key_name = get_defect_key(custom_pk)
                
                # 키 존재 여부 확인
                exists = await redis.exists(key_name)
                if not exists:
                    logger.debug(f"키가 존재하지 않아 삭제하지 않음: {key_name}")
                    continue
                    
                deleted = await redis.delete(key_name)
                if deleted:
                    deleted_count += 1
                    logger.debug(f"성공적으로 삭제됨: {key_name}")
            except Exception as e:
                error_count += 1
                error_msg = f"Redis 삭제 중 에러 발생 (PK: {custom_pk}): {e}"
                error_messages.append(error_msg)
                logger.error(error_msg)

    return {
        "deleted_count": deleted_count,
        "error_count": error_count,
        "error_messages": error_messages,
        "defect_item": request.defect_item
    }
