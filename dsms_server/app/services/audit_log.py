import asyncio
import queue
import threading
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import select
from app.config.database import db_config
from app.models import UserOperationLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AsyncAuditLogWriter:
    """异步审计日志写入器

    使用独立线程和队列实现异步写入，保证不影响主业务逻辑。
    支持重试机制和批量写入，使用异步数据库连接。
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000
    ):
        """
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            batch_size: 批量写入大小
            flush_interval: 强制刷新间隔（秒）
            max_queue_size: 队列最大容量
        """
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self):
        """启动写入线程"""
        if self._running:
            return

        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
            logger.info("AsyncAuditLogWriter started")

    def stop(self):
        """停止写入线程"""
        if not self._running:
            return

        with self._lock:
            if not self._running:
                return
            self._running = False

        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        if self._async_loop and not self._async_loop.is_closed():
            self._async_loop.close()
            self._async_loop = None
        logger.info("AsyncAuditLogWriter stopped")

    def _worker(self):
        """写入线程工作函数"""
        batch = []
        last_flush_time = datetime.now()

        loop = asyncio.new_event_loop()
        self._async_loop = loop
        asyncio.set_event_loop(loop)

        while self._running:
            try:
                try:
                    log_entry = self._queue.get(timeout=1.0)
                    batch.append(log_entry)
                    self._queue.task_done()
                except queue.Empty:
                    pass

                now = datetime.now()
                time_since_flush = (now - last_flush_time).total_seconds()
                should_flush = (
                    len(batch) >= self._batch_size or
                    (batch and time_since_flush >= self._flush_interval)
                )

                if should_flush:
                    loop.run_until_complete(self._async_write_batch(batch))
                    batch.clear()
                    last_flush_time = now

            except Exception as e:
                logger.error(f"Error in audit log worker: {e}")

        if batch:
            loop.run_until_complete(self._async_write_batch(batch))

        if not loop.is_closed():
            loop.close()

    async def _async_write_batch(self, batch: List[dict]):
        """异步批量写入日志"""
        if not batch:
            return

        for attempt in range(self._max_retries):
            try:
                async with db_config.async_session_factory() as session:
                    for log_data in batch:
                        log = UserOperationLog(**log_data)
                        session.add(log)
                    await session.commit()
                logger.debug(f"Async batch write {len(batch)} audit logs")
                return
            except Exception as e:
                logger.warning(f"Async batch write failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        logger.error(f"Failed to write {len(batch)} audit logs after {self._max_retries} retries, writing to fallback file")
        self._write_to_fallback_file(batch)

    def _write_to_fallback_file(self, batch: List[dict]):
        """写入失败时写入到备用文件"""
        try:
            import os
            fallback_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
            os.makedirs(fallback_dir, exist_ok=True)
            fallback_file = os.path.join(fallback_dir, "audit_log_fallback.txt")

            with open(fallback_file, "a", encoding="utf-8") as f:
                for log_data in batch:
                    f.write(f"{datetime.now().isoformat()}: {log_data}\n")
            logger.info(f"Wrote {len(batch)} logs to fallback file")
        except Exception as e:
            logger.error(f"Failed to write to fallback file: {e}")

    def write(
        self,
        user_id: UUID,
        operation_type: str,
        operation_details: Optional[str] = None,
        ip_addr: Optional[str] = None,
        operation_result: str = "success",
        error_msg: Optional[str] = None
    ):
        """将日志写入队列（非阻塞）"""
        if not self._running:
            with self._lock:
                if not self._running and not self._thread:
                    self._running = True
                    self._thread = threading.Thread(target=self._worker, daemon=True)
                    self._thread.start()
                    logger.info("AsyncAuditLogWriter lazy started")

        log_entry = {
            "log_id": uuid4(),
            "user_id": user_id,
            "operation_type": operation_type,
            "operation_details": operation_details,
            "ip_addr": ip_addr,
            "operation_result": operation_result,
            "error_msg": error_msg,
            "created_at": datetime.now()  # naive datetime for asyncpg compatibility
        }

        try:
            self._queue.put_nowait(log_entry)
        except queue.Full:
            logger.warning("Audit log queue is full, dropping log entry")

    def write_success(
        self,
        user_id: UUID,
        operation_type: str,
        operation_details: Optional[str] = None,
        ip_addr: Optional[str] = None
    ):
        """写入成功操作日志"""
        self.write(
            user_id=user_id,
            operation_type=operation_type,
            operation_details=operation_details,
            ip_addr=ip_addr,
            operation_result="success"
        )

    def write_failure(
        self,
        user_id: UUID,
        operation_type: str,
        operation_details: Optional[str] = None,
        ip_addr: Optional[str] = None,
        error_msg: Optional[str] = None
    ):
        """写入失败操作日志"""
        self.write(
            user_id=user_id,
            operation_type=operation_type,
            operation_details=operation_details,
            ip_addr=ip_addr,
            operation_result="fail",
            error_msg=error_msg
        )

    @property
    def queue_size(self) -> int:
        """获取队列当前大小"""
        return self._queue.qsize()


audit_log_writer = AsyncAuditLogWriter(
    max_retries=3,
    retry_delay=1.0,
    batch_size=10,
    flush_interval=5.0,
    max_queue_size=10000
)


class AuditLogService:
    """审计日志服务（用于查询）"""

    @staticmethod
    def get_by_id(log_id: UUID) -> Optional[UserOperationLog]:
        """根据ID获取日志"""
        with db_config.get_session() as session:
            result = session.execute(
                select(UserOperationLog).where(UserOperationLog.log_id == log_id)
            )
            return result.scalars().first()

    @staticmethod
    def get_by_user(
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        operation_type: Optional[str] = None,
        operation_result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UserOperationLog]:
        """获取指定用户的操作日志"""
        with db_config.get_session() as session:
            query = select(UserOperationLog).where(UserOperationLog.user_id == user_id)

            if operation_type:
                query = query.where(UserOperationLog.operation_type == operation_type)

            if operation_result:
                query = query.where(UserOperationLog.operation_result == operation_result)

            if start_date:
                query = query.where(UserOperationLog.created_at >= start_date)

            if end_date:
                query = query.where(UserOperationLog.created_at <= end_date)

            query = query.order_by(UserOperationLog.created_at.desc()).offset(skip).limit(limit)

            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def get_all(
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
        operation_type: Optional[str] = None,
        operation_result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[UserOperationLog]:
        """获取所有操作日志"""
        with db_config.get_session() as session:
            query = select(UserOperationLog)

            if user_id:
                query = query.where(UserOperationLog.user_id == user_id)

            if operation_type:
                query = query.where(UserOperationLog.operation_type == operation_type)

            if operation_result:
                query = query.where(UserOperationLog.operation_result == operation_result)

            if start_date:
                query = query.where(UserOperationLog.created_at >= start_date)

            if end_date:
                query = query.where(UserOperationLog.created_at <= end_date)

            query = query.order_by(UserOperationLog.created_at.desc()).offset(skip).limit(limit)

            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count(
        user_id: Optional[UUID] = None,
        operation_type: Optional[str] = None,
        operation_result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """统计日志数量"""
        with db_config.get_session() as session:
            query = select(UserOperationLog)

            if user_id:
                query = query.where(UserOperationLog.user_id == user_id)

            if operation_type:
                query = query.where(UserOperationLog.operation_type == operation_type)

            if operation_result:
                query = query.where(UserOperationLog.operation_result == operation_result)

            if start_date:
                query = query.where(UserOperationLog.created_at >= start_date)

            if end_date:
                query = query.where(UserOperationLog.created_at <= end_date)

            from sqlalchemy import func
            result = session.execute(select(func.count()).select_from(UserOperationLog))
            return result.scalar()


audit_log_service = AuditLogService()