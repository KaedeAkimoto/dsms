from typing import Optional, List, Dict
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import select, update, delete
from sqlalchemy.orm import joinedload
from app.config.database import db_config
from app.models import DetectionRecord, DefectDetail, ReviewTask, DefectType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DetectionService:
    """检测数据服务"""

    def create_detection_record(
        self,
        device_id: UUID,
        detect_count: Optional[int] = None,
        pass_count: Optional[int] = None,
        detect_info: List = None
    ) -> DetectionRecord:
        """创建检测记录"""
        now = datetime.now(timezone.utc)
        # 生成检测批次ID: BTH[year][month][day][hour][min//time_gap+1]
        # 默认时间间隔为5分钟
        time_gap = 5
        record_batch_id = f"BTH{now.year:04d}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute // time_gap + 1}"

        with db_config.get_session() as session:
            # 检查是否已存在相同批次的记录
            existing_record = session.execute(
                select(DetectionRecord).where(
                    DetectionRecord.record_batch_id == record_batch_id
                )
            ).scalars().first()

            if existing_record:
                # 更新现有记录
                if detect_count is not None:
                    existing_record.detect_count = detect_count
                if pass_count is not None:
                    existing_record.pass_count = pass_count
                if detect_info is not None:
                    existing_record.detect_info = detect_info
                existing_record.latest_upload_at = now
                session.commit()
                session.refresh(existing_record)
                logger.info(f"Detection record updated: {record_batch_id}")
                return existing_record

            # 创建新记录
            record = DetectionRecord(
                record_batch_id=record_batch_id,
                device_id=device_id,
                detect_count=detect_count,
                pass_count=pass_count,
                detect_info=detect_info if detect_info else []
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(f"Detection record created: {record_batch_id}")
            return record

    def get_detection_record(self, record_batch_id: str) -> Optional[DetectionRecord]:
        """根据批次ID获取检测记录"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DetectionRecord)
                .options(joinedload(DetectionRecord.defect_details))
                .where(DetectionRecord.record_batch_id == record_batch_id)
            )
            return result.unique().scalars().first()

    def get_detection_records_by_device(
        self,
        device_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DetectionRecord]:
        """获取设备的检测记录列表"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DetectionRecord)
                .options(joinedload(DetectionRecord.defect_details))
                .where(DetectionRecord.device_id == device_id)
                .order_by(DetectionRecord.latest_upload_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.unique().scalars().all())

    def get_all_detection_records(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[DetectionRecord]:
        """获取所有检测记录"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DetectionRecord)
                .options(joinedload(DetectionRecord.defect_details))
                .order_by(DetectionRecord.latest_upload_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.unique().scalars().all())

    def count_detection_records(self) -> int:
        """统计检测记录数量"""
        with db_config.get_session() as session:
            result = session.execute(select(DetectionRecord))
            return len(result.scalars().all())

    def count_detection_records_by_device(self, device_id: UUID) -> int:
        """统计设备的检测记录数量"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DetectionRecord).where(DetectionRecord.device_id == device_id)
            )
            return len(result.scalars().all())

    def delete_detection_record(self, record_batch_id: str) -> bool:
        """删除检测记录"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DetectionRecord).where(
                    DetectionRecord.record_batch_id == record_batch_id
                )
            )
            record = result.scalars().first()

            if not record:
                return False

            session.delete(record)
            session.commit()
            logger.info(f"Detection record deleted: {record_batch_id}")
            return True

    def create_defect_detail(
        self,
        record_batch_id: str,
        original_img: str,
        defect_count: Optional[int] = None,
        details: List = None
    ) -> DefectDetail:
        """创建缺陷详情"""
        with db_config.get_session() as session:
            defect_detail = DefectDetail(
                defect_details_id=uuid4(),
                record_batch_id=record_batch_id,
                original_img=original_img,
                defect_count=defect_count,
                details=details if details else []
            )
            session.add(defect_detail)
            session.commit()
            session.refresh(defect_detail)
            logger.info(f"Defect detail created: {defect_detail.defect_details_id}")
            return defect_detail

    def get_defect_detail(self, defect_details_id: UUID) -> Optional[DefectDetail]:
        """根据ID获取缺陷详情"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DefectDetail).where(
                    DefectDetail.defect_details_id == defect_details_id
                )
            )
            return result.scalars().first()

    def get_defect_details_by_record(self, record_batch_id: str) -> List[DefectDetail]:
        """获取检测批次的缺陷详情列表"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DefectDetail).where(
                    DefectDetail.record_batch_id == record_batch_id
                )
            )
            return list(result.scalars().all())

    def delete_defect_detail(self, defect_details_id: UUID) -> bool:
        """删除缺陷详情"""
        with db_config.get_session() as session:
            result = session.execute(
                select(DefectDetail).where(
                    DefectDetail.defect_details_id == defect_details_id
                )
            )
            defect_detail = result.scalars().first()

            if not defect_detail:
                return False

            session.delete(defect_detail)
            session.commit()
            logger.info(f"Defect detail deleted: {defect_details_id}")
            return True

    def get_all_defect_types(self) -> List[DefectType]:
        """获取所有缺陷类型"""
        with db_config.get_session() as session:
            result = session.execute(select(DefectType))
            return list(result.scalars().all())

    def create_review_task(
        self,
        defect_details_id: UUID,
        assignee_id: UUID
    ) -> ReviewTask:
        """创建审查任务"""
        with db_config.get_session() as session:
            task = ReviewTask(
                review_task_id=uuid4(),
                defect_details_id=defect_details_id,
                assignee_id=assignee_id,
                assignee_at=datetime.now(timezone.utc)
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info(f"Review task created: {task.review_task_id}")
            return task

    def get_review_task(self, review_task_id: UUID) -> Optional[ReviewTask]:
        """根据ID获取审查任务"""
        with db_config.get_session() as session:
            result = session.execute(
                select(ReviewTask).where(
                    ReviewTask.review_task_id == review_task_id
                )
            )
            return result.scalars().first()

    def get_review_tasks_by_assignee(
        self,
        assignee_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReviewTask]:
        """获取用户的审查任务列表"""
        with db_config.get_session() as session:
            result = session.execute(
                select(ReviewTask)
                .where(ReviewTask.assignee_id == assignee_id)
                .order_by(ReviewTask.assignee_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())

    def get_all_review_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ReviewTask]:
        """获取所有审查任务"""
        with db_config.get_session() as session:
            query = select(ReviewTask).order_by(ReviewTask.assignee_at.desc())
            
            if status:
                query = query.where(ReviewTask.review_status == status)
            
            result = session.execute(query.offset(skip).limit(limit))
            return list(result.scalars().all())

    def update_review_task(
        self,
        review_task_id: UUID,
        reviewer_id: Optional[UUID] = None,
        review_status: Optional[str] = None,
        review_result: Optional[str] = None,
        review_defect_count: Optional[int] = None,
        has_details: Optional[bool] = None,
        review_details: Optional[List] = None,
        review_comment: Optional[str] = None
    ) -> Optional[ReviewTask]:
        """更新审查任务"""
        VALID_STATUS = {"pending", "completed", "cancel", "timeout"}
        VALID_RESULT = {"confirmed", "false_positive", "uncertain", "confusion"}
        
        with db_config.get_session() as session:
            result = session.execute(
                select(ReviewTask).options(
                    joinedload(ReviewTask.defect_detail)
                ).where(
                    ReviewTask.review_task_id == review_task_id
                )
            )
            task = result.scalars().first()

            if not task:
                return None

            original_status = task.review_status
            
            if review_status is not None:
                if review_status not in VALID_STATUS:
                    raise ValueError(f"无效的审查状态: {review_status}，有效值: {VALID_STATUS}")
                
                allowed_transitions = {
                    "pending": {"pending", "completed", "cancel", "timeout"},
                    "completed": {"completed"},
                    "cancel": {"cancel"},
                    "timeout": {"pending", "completed", "cancel"}
                }
                
                if review_status not in allowed_transitions.get(original_status, set()):
                    raise ValueError(f"状态转换不允许: {original_status} -> {review_status}")
                
                task.review_status = review_status
                
                if review_status == "completed" and not task.completed_at:
                    task.completed_at = datetime.now(timezone.utc)

            if review_result is not None:
                if review_result not in VALID_RESULT:
                    raise ValueError(f"无效的审查结果: {review_result}，有效值: {VALID_RESULT}")
                task.review_result = review_result

            if reviewer_id is not None:
                task.reviewer_id = reviewer_id

            if review_defect_count is not None:
                if review_defect_count < 0:
                    raise ValueError("缺陷数量不能为负数")
                task.review_defect_count = review_defect_count

            if has_details is not None:
                task.has_details = has_details
                if not has_details:
                    task.review_details = None

            if review_details is not None:
                if not isinstance(review_details, list):
                    raise ValueError("review_details必须是列表格式")
                for item in review_details:
                    if not isinstance(item, dict) or 'defect_type_id' not in item:
                        raise ValueError("review_details格式不正确，需要包含defect_type_id")
                task.review_details = review_details
                task.has_details = True

                defect_detail = task.defect_detail
                if defect_detail:
                    original_defect_count = defect_detail.defect_count or 0
                    defect_detail.details = review_details
                    
                    if review_defect_count is not None:
                        defect_detail.defect_count = review_defect_count
                    else:
                        review_defect_count = len(review_details)
                        defect_detail.defect_count = review_defect_count

                    detection_record = defect_detail.detection_record
                    if detection_record:
                        count_diff = review_defect_count - original_defect_count
                        detection_record.detect_count = (detection_record.detect_count or 0) + count_diff
                        
                        type_counts = {}
                        for detail in review_details:
                            defect_type_id = detail['defect_type_id']
                            type_counts[defect_type_id] = type_counts.get(defect_type_id, 0) + 1
                        
                        detection_record.detect_info = [
                            {'defect_type_id': k, 'defect_count': v} 
                            for k, v in type_counts.items()
                        ]
            elif review_defect_count is not None:
                defect_detail = task.defect_detail
                if defect_detail:
                    original_defect_count = defect_detail.defect_count or 0
                    defect_detail.defect_count = review_defect_count
                    
                    detection_record = defect_detail.detection_record
                    if detection_record:
                        count_diff = review_defect_count - original_defect_count
                        detection_record.detect_count = (detection_record.detect_count or 0) + count_diff

            if review_comment is not None:
                task.review_comment = review_comment

            session.commit()
            session.refresh(task)
            logger.info(f"Review task updated: {review_task_id}")
            return task

    def count_review_tasks(self, status: Optional[str] = None) -> int:
        """统计审查任务数量"""
        with db_config.get_session() as session:
            query = select(ReviewTask)
            if status:
                query = query.where(ReviewTask.review_status == status)
            result = session.execute(query)
            return len(result.scalars().all())

    def count_review_tasks_by_assignee(self, assignee_id: UUID) -> int:
        """统计用户的审查任务数量"""
        with db_config.get_session() as session:
            result = session.execute(
                select(ReviewTask).where(ReviewTask.assignee_id == assignee_id)
            )
            return len(result.scalars().all())

    def transfer_review_task(
        self,
        review_task_id: UUID,
        new_assignee_id: UUID
    ) -> Optional[ReviewTask]:
        """移交审查任务"""
        with db_config.get_session() as session:
            result = session.execute(
                select(ReviewTask).where(
                    ReviewTask.review_task_id == review_task_id
                )
            )
            task = result.scalars().first()

            if not task:
                return None

            # 只有待处理或已提交的任务可以移交
            if task.review_status not in ['pending', 'submitted']:
                return None

            task.assignee_id = new_assignee_id
            task.assignee_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(task)
            logger.info(f"Review task transferred: {review_task_id} to {new_assignee_id}")
            return task

    def get_detection_records_by_time(
        self,
        start_time: str,
        end_time: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DetectionRecord]:
        """按时间范围查询检测记录"""
        from sqlalchemy import func
        with db_config.get_session() as session:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            query = (
                select(DetectionRecord)
                .options(joinedload(DetectionRecord.defect_details))
                .where(
                    DetectionRecord.latest_upload_at >= start_dt,
                    DetectionRecord.latest_upload_at <= end_dt
                )
                .order_by(DetectionRecord.latest_upload_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = session.execute(query)
            return list(result.unique().scalars().all())

    def count_detection_records_by_time(self, start_time: str, end_time: str) -> int:
        """统计时间范围内的检测记录数量"""
        from sqlalchemy import func
        with db_config.get_session() as session:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            query = select(func.count(DetectionRecord.record_batch_id)).where(
                DetectionRecord.latest_upload_at >= start_dt,
                DetectionRecord.latest_upload_at <= end_dt
            )
            result = session.execute(query)
            return result.scalar() or 0

    def get_detection_records_by_defect_type(
        self,
        defect_type_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[DetectionRecord]:
        """按缺陷类型查询检测记录"""
        from sqlalchemy import cast, String
        with db_config.get_session() as session:
            query = (
                select(DetectionRecord)
                .options(joinedload(DetectionRecord.defect_details))
                .join(DefectDetail, DetectionRecord.record_batch_id == DefectDetail.record_batch_id)
                .where(
                    cast(DefectDetail.details, String).like(f'%"defect_type_id": {defect_type_id}%')
                )
                .order_by(DetectionRecord.latest_upload_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = session.execute(query)
            return list(result.unique().scalars().all())

    def count_detection_records_by_defect_type(self, defect_type_id: int) -> int:
        """统计指定缺陷类型的检测记录数量"""
        from sqlalchemy import func, cast, String
        with db_config.get_session() as session:
            query = (
                select(func.count(DetectionRecord.record_batch_id.distinct()))
                .join(DefectDetail, DetectionRecord.record_batch_id == DefectDetail.record_batch_id)
                .where(
                    cast(DefectDetail.details, String).like(f'%"defect_type_id": {defect_type_id}%')
                )
            )
            result = session.execute(query)
            return result.scalar() or 0

    def get_defect_stats(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict]:
        """获取缺陷统计数据"""
        with db_config.get_session() as session:
            defect_types = session.execute(
                select(DefectType.defect_type_id, DefectType.defect_type_name)
            ).all()

            stats_dict = {dt.defect_type_id: {
                'defect_type_id': dt.defect_type_id,
                'defect_type_name': dt.defect_type_name,
                'count': 0
            } for dt in defect_types}

            query = select(DefectDetail).options(joinedload(DefectDetail.detection_record))

            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                query = query.join(DetectionRecord).where(
                    DetectionRecord.latest_upload_at >= start_dt,
                    DetectionRecord.latest_upload_at <= end_dt
                )

            defect_details = session.execute(query).unique().scalars().all()

            for detail in defect_details:
                if detail.details and isinstance(detail.details, list):
                    for item in detail.details:
                        if isinstance(item, dict) and 'defect_type_id' in item:
                            defect_type_id = item['defect_type_id']
                            if defect_type_id in stats_dict:
                                stats_dict[defect_type_id]['count'] += 1

            return list(stats_dict.values())

    def get_detection_trend(
        self,
        start_time: str,
        end_time: str,
        group_by: str = "day"
    ) -> List[Dict]:
        """按时间分组获取检测趋势"""
        from sqlalchemy import func, extract
        with db_config.get_session() as session:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            if group_by == "day":
                date_expr = func.date(DetectionRecord.latest_upload_at)
            elif group_by == "week":
                date_expr = func.date_trunc('week', DetectionRecord.latest_upload_at)
            elif group_by == "month":
                date_expr = func.date_trunc('month', DetectionRecord.latest_upload_at)
            else:
                date_expr = func.date(DetectionRecord.latest_upload_at)

            query = (
                select(
                    date_expr.label('date'),
                    func.count(DetectionRecord.record_batch_id).label('total_count'),
                    func.sum(DetectionRecord.detect_count).label('detect_sum'),
                    func.sum(DetectionRecord.pass_count).label('pass_sum')
                )
                .where(
                    DetectionRecord.latest_upload_at >= start_dt,
                    DetectionRecord.latest_upload_at <= end_dt
                )
                .group_by(date_expr)
                .order_by(date_expr)
            )

            result = session.execute(query)
            trend = []
            for row in result:
                trend.append({
                    "date": row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
                    "total_count": row.total_count,
                    "detect_sum": row.detect_sum or 0,
                    "pass_sum": row.pass_sum or 0
                })

            return trend

    def get_defect_trend_by_day(
        self,
        start_time: str,
        end_time: str
    ) -> List[Dict]:
        """按天统计各类型缺陷数量"""
        from sqlalchemy import func
        with db_config.get_session() as session:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            defect_types = session.execute(
                select(DefectType.defect_type_id, DefectType.defect_type_name)
            ).all()

            defect_type_map = {dt.defect_type_id: dt.defect_type_name for dt in defect_types}
            all_defect_type_ids = list(defect_type_map.keys())

            date_query = (
                select(
                    func.date(DetectionRecord.latest_upload_at).label('date')
                )
                .where(
                    DetectionRecord.latest_upload_at >= start_dt,
                    DetectionRecord.latest_upload_at <= end_dt
                )
                .group_by(func.date(DetectionRecord.latest_upload_at))
                .order_by(func.date(DetectionRecord.latest_upload_at))
            )
            dates_result = session.execute(date_query).all()
            dates = [row.date for row in dates_result]

            defect_details_query = (
                select(DefectDetail)
                .options(joinedload(DefectDetail.detection_record))
                .join(DetectionRecord)
                .where(
                    DetectionRecord.latest_upload_at >= start_dt,
                    DetectionRecord.latest_upload_at <= end_dt
                )
            )
            defect_details = session.execute(defect_details_query).unique().scalars().all()

            stats_map = {}
            for detail in defect_details:
                if detail.details and isinstance(detail.details, list):
                    record_date = func.date(detail.detection_record.latest_upload_at)
                    for item in detail.details:
                        if isinstance(item, dict) and 'defect_type_id' in item:
                            defect_type_id = item['defect_type_id']
                            if defect_type_id in all_defect_type_ids:
                                date_key = detail.detection_record.latest_upload_at.date()
                                key = (date_key, defect_type_id)
                                stats_map[key] = stats_map.get(key, 0) + 1

            result = []
            for date in dates:
                date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                day_defects = []
                for defect_type_id in all_defect_type_ids:
                    count = stats_map.get((date, defect_type_id), 0)
                    day_defects.append({
                        "defect_type_id": defect_type_id,
                        "defect_type_name": defect_type_map[defect_type_id],
                        "count": count
                    })
                result.append({
                    "date": date_str,
                    "defects": day_defects
                })

            if not result:
                first_date = start_dt.date()
                last_date = end_dt.date()
                current = first_date
                while current <= last_date:
                    date_str = current.isoformat()
                    day_defects = []
                    for defect_type_id in all_defect_type_ids:
                        day_defects.append({
                            "defect_type_id": defect_type_id,
                            "defect_type_name": defect_type_map[defect_type_id],
                            "count": 0
                        })
                    result.append({
                        "date": date_str,
                        "defects": day_defects
                    })
                    current = current + __import__('datetime').timedelta(days=1)

            return result


detection_service = DetectionService()