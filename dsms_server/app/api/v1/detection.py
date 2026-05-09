import base64
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.responses import SuccessResponse
from app.core.middlewares import require_permission
from app.core.system_roles import api
from app.schemas.detection import (
    DetectionRecordResponse,
    DetectionRecordListResponse,
    DefectTypeResponse,
    ReviewTaskResponse,
    ReviewTaskListResponse,
    ReviewTaskUpdateRequest,
    ReviewTaskTransferRequest,
    ReviewTaskCreateRequest
)
from app.services.detection import detection_service
from app.services.audit_log import audit_log_writer
from app.services.message import user_message_service

router = APIRouter()


@api(
    path="/detection-records",
    method="GET",
    name="获取检测记录列表",
    description="分页获取检测记录列表",
    tags=["检测数据"]
)
@router.get("/detection-records")
async def get_detection_records(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取检测记录列表"""
    records = detection_service.get_all_detection_records(skip=skip, limit=limit)
    total = detection_service.count_detection_records()

    return SuccessResponse(
        data=DetectionRecordListResponse(
            total=total,
            records=[DetectionRecordResponse.from_orm(r).model_dump(mode="json") for r in records]
        ).model_dump(mode='json'),
        message="获取检测记录成功"
    )


@api(
    path="/detection-records/by-time",
    method="GET",
    name="按时间范围查询检测记录",
    description="根据时间段筛选检测记录",
    tags=["检测数据"]
)
@router.get("/detection-records/by-time")
async def get_detection_records_by_time(
    start_time: str = Query(..., description="开始时间（ISO 8601格式）"),
    end_time: str = Query(..., description="结束时间（ISO 8601格式）"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """根据时间段筛选检测记录"""
    records = detection_service.get_detection_records_by_time(
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    total = detection_service.count_detection_records_by_time(start_time, end_time)

    return SuccessResponse(
        data=DetectionRecordListResponse(
            total=total,
            records=[DetectionRecordResponse.from_orm(r).model_dump(mode="json") for r in records]
        ).model_dump(mode='json'),
        message="获取检测记录成功"
    )


@api(
    path="/detection-records/by-defect-type/{defect_type_id}",
    method="GET",
    name="按缺陷类型查询记录",
    description="根据缺陷类型筛选检测记录",
    tags=["检测数据"]
)
@router.get("/detection-records/by-defect-type/{defect_type_id}")
async def get_detection_records_by_defect_type(
    defect_type_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """根据缺陷类型筛选检测记录"""
    records = detection_service.get_detection_records_by_defect_type(
        defect_type_id=defect_type_id,
        skip=skip,
        limit=limit
    )
    total = detection_service.count_detection_records_by_defect_type(defect_type_id)

    return SuccessResponse(
        data=DetectionRecordListResponse(
            total=total,
            records=[DetectionRecordResponse.from_orm(r).model_dump(mode="json") for r in records]
        ).model_dump(mode='json'),
        message="获取缺陷类型记录成功"
    )


@api(
    path="/detection-records/{record_batch_id}",
    method="GET",
    name="获取检测记录详情",
    description="获取检测记录详情",
    tags=["检测数据"]
)
@router.get("/detection-records/{record_batch_id}")
async def get_detection_record(
    record_batch_id: str,
    user=Depends(require_permission)
):
    """获取检测记录详情"""
    record = detection_service.get_detection_record(record_batch_id)
    if not record:
        raise HTTPException(status_code=404, detail="检测记录不存在")

    return SuccessResponse(
        data=DetectionRecordResponse.from_orm(record).model_dump(mode="json"),
        message="获取检测记录成功"
    )


@api(
    path="/detection-records/query/by-device/{device_id}",
    method="GET",
    name="获取设备检测记录",
    description="获取指定设备的检测记录列表",
    tags=["检测数据"]
)
@router.get("/detection-records/query/by-device/{device_id}")
async def get_device_detection_records(
    device_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取设备检测记录列表"""
    records = detection_service.get_detection_records_by_device(
        device_id=device_id,
        skip=skip,
        limit=limit
    )
    total = detection_service.count_detection_records_by_device(device_id)

    return SuccessResponse(
        data=DetectionRecordListResponse(
            total=total,
            records=[DetectionRecordResponse.from_orm(r).model_dump(mode="json") for r in records]
        ).model_dump(mode='json'),
        message="获取设备检测记录成功"
    )


@api(
    path="/defect-details/{defect_details_id}",
    method="GET",
    name="获取缺陷详情",
    description="获取缺陷详情",
    tags=["检测数据"]
)
@router.get("/defect-details/{defect_details_id}")
async def get_defect_detail(
    defect_details_id: UUID,
    user=Depends(require_permission)
):
    """获取缺陷详情"""
    defect_detail = detection_service.get_defect_detail(defect_details_id)
    if not defect_detail:
        raise HTTPException(status_code=404, detail="缺陷详情不存在")

    def encode_image(img_data) -> str:
        if img_data is None:
            return ''
        try:
            if isinstance(img_data, (bytes, bytearray)):
                return base64.b64encode(img_data).decode('utf-8')
            else:
                return base64.b64encode(bytes(img_data)).decode('utf-8')
        except Exception:
            return ''

    return SuccessResponse(
        data={
            'defect_details_id': str(defect_detail.defect_details_id),
            'record_batch_id': defect_detail.record_batch_id,
            'image_base64': encode_image(defect_detail.image),
            'image_format': defect_detail.image_format,
            'defect_count': defect_detail.defect_count,
            'details': defect_detail.details
        },
        message="获取缺陷详情成功"
    )


@api(
    path="/defect-types",
    method="GET",
    name="获取缺陷类型列表",
    description="获取所有缺陷类型",
    tags=["检测数据"]
)
@router.get("/defect-types")
async def get_defect_types(user=Depends(require_permission)):
    """获取缺陷类型列表"""
    defect_types = detection_service.get_all_defect_types()

    return SuccessResponse(
        data=[
            DefectTypeResponse(
                defect_type_id=d.defect_type_id,
                defect_type_name=d.defect_type_name
            ).model_dump(mode='json')
            for d in defect_types
        ],
        message="获取缺陷类型成功"
    )


@api(
    path="/review-tasks",
    method="GET",
    name="获取审查任务列表",
    description="分页获取审查任务列表",
    tags=["检测数据"]
)
@router.get("/review-tasks")
async def get_review_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="审查状态过滤"),
    user=Depends(require_permission)
):
    """获取审查任务列表"""
    tasks = detection_service.get_all_review_tasks(
        skip=skip,
        limit=limit,
        status=status
    )
    total = detection_service.count_review_tasks(status=status)

    return SuccessResponse(
        data=ReviewTaskListResponse(
            total=total,
            tasks=[ReviewTaskResponse.from_orm(t).model_dump(mode="json") for t in tasks]
        ).model_dump(mode='json'),
        message="获取审查任务成功"
    )


@api(
    path="/review-tasks/me",
    method="GET",
    name="获取我的审查任务",
    description="获取当前用户的审查任务列表",
    tags=["检测数据"]
)
@router.get("/review-tasks/me")
async def get_my_review_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user=Depends(require_permission)
):
    """获取当前用户的审查任务列表"""
    tasks = detection_service.get_review_tasks_by_assignee(
        assignee_id=user["user_id"],
        skip=skip,
        limit=limit
    )
    total = detection_service.count_review_tasks_by_assignee(user["user_id"])

    return SuccessResponse(
        data=ReviewTaskListResponse(
            total=total,
            tasks=[ReviewTaskResponse.from_orm(t).model_dump(mode="json") for t in tasks]
        ).model_dump(mode='json'),
        message="获取我的审查任务成功"
    )


@api(
    path="/review-tasks",
    method="POST",
    name="创建审查任务",
    description="创建审查任务，将缺陷分配给质检员进行人工审查",
    tags=["检测数据"]
)
@router.post("/review-tasks")
async def create_review_task(
    request: ReviewTaskCreateRequest,
    user=Depends(require_permission)
):
    """创建审查任务"""
    # 检查缺陷详情是否存在
    defect_detail = detection_service.get_defect_detail(request.defect_details_id)
    if not defect_detail:
        raise HTTPException(status_code=404, detail="缺陷详情不存在")

    # 创建审查任务
    task = detection_service.create_review_task(
        defect_details_id=request.defect_details_id,
        assignee_id=request.assignee_id
    )

    # 发送消息通知被分配人
    try:
        user_message_service.create_message(
            send_user=user["user_id"],
            receive_user=request.assignee_id,
            content=f"您收到一个新的审查任务，请及时处理。"
        )
    except Exception:
        pass

    # 写入审计日志
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="创建审查任务",
        operation_details=f"创建审查任务：缺陷详情ID {request.defect_details_id}，分配给 {request.assignee_id}"
    )

    return SuccessResponse(
        data=ReviewTaskResponse.from_orm(task).model_dump(mode="json"),
        message="审查任务创建成功"
    )


@api(
    path="/review-tasks/{review_task_id}",
    method="GET",
    name="获取审查任务详情",
    description="获取审查任务详情",
    tags=["检测数据"]
)
@router.get("/review-tasks/{review_task_id}")
async def get_review_task(
    review_task_id: UUID,
    user=Depends(require_permission)
):
    """获取审查任务详情"""
    task = detection_service.get_review_task(review_task_id)
    if not task:
        raise HTTPException(status_code=404, detail="审查任务不存在")

    return SuccessResponse(
        data=ReviewTaskResponse.from_orm(task).model_dump(mode="json"),
        message="获取审查任务成功"
    )


@api(
    path="/review-tasks/{review_task_id}",
    method="PUT",
    name="更新审查任务",
    description="更新审查任务状态和结果",
    tags=["检测数据"]
)
@router.put("/review-tasks/{review_task_id}")
async def update_review_task(
    review_task_id: UUID,
    request: ReviewTaskUpdateRequest,
    user=Depends(require_permission)
):
    """更新审查任务"""
    try:
        task = detection_service.update_review_task(
            review_task_id=review_task_id,
            reviewer_id=request.reviewer_id,
            review_status=request.review_status,
            review_result=request.review_result,
            review_defect_count=request.review_defect_count,
            has_details=request.has_details,
            review_details=request.review_details,
            review_comment=request.review_comment
        )

        if not task:
            audit_log_writer.write_failure(
                user_id=user["user_id"],
                operation_type="更新审查任务",
                operation_details=f"更新审查任务失败：任务ID {review_task_id} 不存在",
                error_msg="审查任务不存在"
            )
            raise HTTPException(status_code=404, detail="审查任务不存在")

        # 发送消息通知任务负责人
        try:
            assignee = task.assignee_id
            reviewer = request.reviewer_id or user["user_id"]
            status_text = "已完成" if request.review_status == "completed" else \
                         "已取消" if request.review_status == "cancel" else \
                         "已超时" if request.review_status == "timeout" else "待审查"
            user_message_service.create_message(
                send_user=reviewer,
                receive_user=assignee,
                content=f"您的审查任务已更新，状态：{status_text}，结果：{request.review_result or '无'}。"
            )
        except Exception:
            pass

        # 写入审计日志
        audit_log_writer.write_success(
            user_id=user["user_id"],
            operation_type="更新审查任务",
            operation_details=f"更新审查任务：任务ID {review_task_id}，状态 {request.review_status}，结果 {request.review_result}"
        )

        return SuccessResponse(
            data=ReviewTaskResponse.from_orm(task).model_dump(mode="json"),
            message="审查任务更新成功"
        )
    
    except ValueError as e:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="更新审查任务",
            operation_details=f"更新审查任务失败：{str(e)}",
            error_msg=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))


@api(
    path="/review-tasks/{review_task_id}/transfer",
    method="POST",
    name="移交审查任务",
    description="将审查任务移交给其他人",
    tags=["检测数据"]
)
@router.post("/review-tasks/{review_task_id}/transfer")
async def transfer_review_task(
    review_task_id: UUID,
    request: ReviewTaskTransferRequest,
    user=Depends(require_permission)
):
    """移交审查任务"""
    task = detection_service.transfer_review_task(
        review_task_id=review_task_id,
        new_assignee_id=request.new_assignee_id
    )

    if not task:
        audit_log_writer.write_failure(
            user_id=user["user_id"],
            operation_type="移交审查任务",
            operation_details=f"移交审查任务失败: 任务ID {review_task_id}",
            error_msg="任务不存在或状态不允许移交"
        )
        raise HTTPException(status_code=404, detail="任务不存在或状态不允许移交")

    # 发送消息给新负责人
    try:
        user_message_service.create_message(
            send_user=user["user_id"],
            receive_user=request.new_assignee_id,
            content=f"您收到一个移交的审查任务: 任务ID {review_task_id}"
        )
    except Exception:
        pass

    # 写入审计日志
    audit_log_writer.write_success(
        user_id=user["user_id"],
        operation_type="移交审查任务",
        operation_details=f"移交审查任务: 任务ID {review_task_id} 移交给 {request.new_assignee_id}"
    )

    return SuccessResponse(
        data=ReviewTaskResponse.from_orm(task).model_dump(mode="json"),
        message="移交成功"
    )


@api(
    path="/detection/defect-stats",
    method="GET",
    name="缺陷统计接口",
    description="统计各类型缺陷数量",
    tags=["检测数据"]
)
@router.get("/detection/defect-stats")
async def get_defect_stats(
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    user=Depends(require_permission)
):
    """统计各类型缺陷数量"""
    stats = detection_service.get_defect_stats(start_time, end_time)
    return SuccessResponse(
        data=stats,
        message="获取缺陷统计成功"
    )


@api(
    path="/detection/trend",
    method="GET",
    name="检测趋势接口",
    description="按时间分组统计检测数据",
    tags=["检测数据"]
)
@router.get("/detection/trend")
async def get_detection_trend(
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    group_by: str = Query("day", description="分组方式：day、week、month"),
    user=Depends(require_permission)
):
    """按时间分组统计检测数据"""
    trend = detection_service.get_detection_trend(start_time, end_time, group_by)
    return SuccessResponse(
        data=trend,
        message="获取检测趋势成功"
    )


@api(
    path="/detection/defect-trend",
    method="GET",
    name="按天统计缺陷趋势",
    description="按天统计各类型缺陷数量",
    tags=["检测数据"]
)
@router.get("/detection/defect-trend")
async def get_defect_trend(
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    user=Depends(require_permission)
):
    """按天统计各类型缺陷数量"""
    trend = detection_service.get_defect_trend_by_day(start_time, end_time)
    return SuccessResponse(
        data=trend,
        message="获取缺陷趋势成功"
    )