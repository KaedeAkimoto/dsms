"""
消息服务模块
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlmodel import select, delete
import asyncio

from app.config.database import db_config
from app.models.models import (
    SystemMessage,
    Announcement,
    AnnouncementReader,
    UserMessage,
    User
)


class SSEPushManager:
    """SSE推送管理器"""

    @staticmethod
    async def push_message(user_id: UUID, message_type: str, data: dict):
        """推送消息到指定用户的SSE连接"""
        try:
            from app.core.connection_manager import sse_connection_manager
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await sse_connection_manager.send_personal_message(message, user_id)
        except Exception:
            pass

    @staticmethod
    def push_message_sync(user_id: UUID, message_type: str, data: dict):
        """同步推送消息（创建后台任务）"""
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            asyncio.create_task(
                SSEPushManager.push_message(user_id, message_type, data)
            )
        except RuntimeError:
            pass
        except Exception:
            pass


class SystemMessageService:
    """系统消息服务"""

    @staticmethod
    def create_message(receive_user: UUID, content: str) -> SystemMessage:
        """创建系统消息"""
        with db_config.get_session() as session:
            message = SystemMessage(
                receive_user=receive_user,
                content=content
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            msg_dict = {
                "message_id": str(message.msg_id),
                "content": message.content,
                "status": message.status,
                "created_at": message.created_at.isoformat() if message.created_at else None
            }
            SSEPushManager.push_message_sync(
                receive_user,
                "system_message",
                msg_dict
            )
            return message

    @staticmethod
    def batch_create_messages(user_ids: List[UUID], content: str) -> List[SystemMessage]:
        """批量创建系统消息"""
        messages = []
        with db_config.get_session() as session:
            for user_id in user_ids:
                message = SystemMessage(
                    receive_user=user_id,
                    content=content
                )
                session.add(message)
                messages.append(message)
            session.commit()
            for message in messages:
                session.refresh(message)
        for message in messages:
            msg_dict = {
                "message_id": str(message.msg_id),
                "content": message.content,
                "status": message.status,
                "created_at": message.created_at.isoformat() if message.created_at else None
            }
            SSEPushManager.push_message_sync(
                message.receive_user,
                "system_message",
                msg_dict
            )
        return messages

    @staticmethod
    def get_user_messages(user_id: UUID, skip: int = 0, limit: int = 100) -> List[SystemMessage]:
        """获取用户的系统消息"""
        with db_config.get_session() as session:
            query = select(SystemMessage).where(
                SystemMessage.receive_user == user_id
            ).order_by(SystemMessage.created_at.desc()).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_user_messages(user_id: UUID, status: Optional[str] = None) -> int:
        """统计用户的系统消息数量"""
        with db_config.get_session() as session:
            query = select(SystemMessage).where(SystemMessage.receive_user == user_id)
            if status:
                query = query.where(SystemMessage.status == status)
            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def get_message_by_id(msg_id: UUID) -> Optional[SystemMessage]:
        """根据ID获取消息"""
        with db_config.get_session() as session:
            return session.get(SystemMessage, msg_id)

    @staticmethod
    def mark_as_read(msg_id: UUID) -> bool:
        """标记消息为已读"""
        with db_config.get_session() as session:
            message = session.get(SystemMessage, msg_id)
            if not message:
                return False
            message.status = "read"
            message.readed_at = datetime.now(timezone.utc)
            session.add(message)
            session.commit()
            return True

    @staticmethod
    def mark_all_as_read(user_id: UUID) -> int:
        """标记用户所有消息为已读"""
        with db_config.get_session() as session:
            query = select(SystemMessage).where(
                SystemMessage.receive_user == user_id,
                SystemMessage.status == "unread"
            )
            result = session.execute(query)
            messages = list(result.scalars().all())
            for message in messages:
                message.status = "read"
                message.readed_at = datetime.now(timezone.utc)
                session.add(message)
            session.commit()
            return len(messages)

    @staticmethod
    def delete_message(msg_id: UUID) -> bool:
        """删除消息"""
        with db_config.get_session() as session:
            message = session.get(SystemMessage, msg_id)
            if not message:
                return False
            session.delete(message)
            session.commit()
            return True


class AnnouncementService:
    """公告服务"""

    @staticmethod
    def create_announcement(
        receiver_type: str,
        receive_target: Optional[int],
        content: str,
        send_user: UUID,
        expired: Optional[datetime] = None
    ) -> Announcement:
        """创建公告"""
        # 如果没有设置过期时间，默认7天后过期
        if expired is None:
            expired = datetime.now() + timedelta(days=7)
        
        with db_config.get_session() as session:
            announcement = Announcement(
                receiver_type=receiver_type,
                receive_target=receive_target,
                content=content,
                send_user=send_user,
                expired=expired
            )
            session.add(announcement)
            session.commit()
            session.refresh(announcement)
            return announcement

    @staticmethod
    def get_all_announcements(skip: int = 0, limit: int = 100) -> List[Announcement]:
        """获取所有公告（不过滤过期状态）"""
        with db_config.get_session() as session:
            query = select(Announcement).order_by(Announcement.created_at.desc()).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def get_announcements_for_admin(
        user_id: UUID,
        role_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Announcement]:
        """获取公告列表（管理员用，包含过期公告权限控制）

        规则：
        - 未过期的公告：所有用户可见
        - 已过期的公告：仅发送者或管理员角色可见
        """
        with db_config.get_session() as session:
            now = datetime.now()
            query = select(Announcement).order_by(Announcement.created_at.desc()).offset(skip).limit(limit)
            result = session.execute(query)
            announcements = list(result.scalars().all())

            filtered = []
            admin_roles = ["hr_admin", "senior_sys_admin", "super_sys_admin"]
            for ann in announcements:
                if ann.expired > now:
                    filtered.append(ann)
                else:
                    if ann.send_user == user_id or role_id in admin_roles:
                        filtered.append(ann)

            return filtered

    @staticmethod
    def count_announcements() -> int:
        """统计公告数量"""
        with db_config.get_session() as session:
            query = select(Announcement)
            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def get_announcement_by_id(announcement_id: UUID) -> Optional[Announcement]:
        """根据ID获取公告"""
        with db_config.get_session() as session:
            return session.get(Announcement, announcement_id)

    @staticmethod
    def can_view_announcement(
        announcement_id: UUID,
        user_id: UUID,
        role_id: str
    ) -> bool:
        """检查用户是否有权限查看公告（考虑过期状态）

        规则：
        - 未过期的公告：所有能收到该公告的用户可查看
        - 已过期的公告：仅发送者或管理员角色可查看
        """
        with db_config.get_session() as session:
            announcement = session.get(Announcement, announcement_id)
            if not announcement:
                return False

            now = datetime.now()
            if announcement.expired > now:
                user = session.get(User, user_id)
                if not user:
                    return False
                if announcement.receiver_type == "all":
                    return True
                elif announcement.receiver_type == "department":
                    return user.department_id == announcement.receive_target
                elif announcement.receiver_type == "role":
                    return user.role_id == announcement.receive_target
                elif announcement.receiver_type == "title":
                    return user.title_id == announcement.receive_target
                return False
            else:
                admin_roles = ["hr_admin", "senior_sys_admin", "super_sys_admin"]
                return announcement.send_user == user_id or role_id in admin_roles

    @staticmethod
    def get_user_announcements(user_id: UUID, skip: int = 0, limit: int = 100) -> List[Announcement]:
        """获取用户可见的公告"""
        with db_config.get_session() as session:
            # 获取用户信息
            user = session.get(User, user_id)
            if not user:
                return []

            # 查询用户可见的公告
            query = select(Announcement).where(
                (Announcement.receiver_type == "all") |
                (Announcement.receiver_type == "department") & (Announcement.receive_target == user.department_id) |
                (Announcement.receiver_type == "role") & (Announcement.receive_target == user.role_id) |
                (Announcement.receiver_type == "title") & (Announcement.receive_target == user.title_id)
            ).where(
                Announcement.expired > datetime.now()
            ).order_by(Announcement.created_at.desc()).offset(skip).limit(limit)

            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_user_announcements(user_id: UUID) -> int:
        """统计用户可见的公告数量"""
        with db_config.get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return 0

            query = select(Announcement).where(
                (Announcement.receiver_type == "all") |
                (Announcement.receiver_type == "department") & (Announcement.receive_target == user.department_id) |
                (Announcement.receiver_type == "role") & (Announcement.receive_target == user.role_id) |
                (Announcement.receiver_type == "title") & (Announcement.receive_target == user.title_id)
            ).where(Announcement.expired > datetime.now())

            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def update_announcement(announcement_id: UUID, **kwargs) -> Optional[Announcement]:
        """更新公告"""
        with db_config.get_session() as session:
            announcement = session.get(Announcement, announcement_id)
            if not announcement:
                return None

            for key, value in kwargs.items():
                if value is not None and hasattr(announcement, key):
                    setattr(announcement, key, value)

            session.add(announcement)
            session.commit()
            session.refresh(announcement)
            return announcement

    @staticmethod
    def delete_announcement(announcement_id: UUID) -> bool:
        """删除公告"""
        with db_config.get_session() as session:
            announcement = session.get(Announcement, announcement_id)
            if not announcement:
                return False
            delete_readers_query = delete(AnnouncementReader).where(
                AnnouncementReader.announcement_id == announcement_id
            )
            session.execute(delete_readers_query)
            session.delete(announcement)
            session.commit()
            return True

    @staticmethod
    def mark_as_read(announcement_id: UUID, user_id: UUID) -> bool:
        """标记公告为已读"""
        with db_config.get_session() as session:
            # 检查是否已存在记录
            query = select(AnnouncementReader).where(
                AnnouncementReader.announcement_id == announcement_id,
                AnnouncementReader.user_id == user_id
            )
            result = session.execute(query)
            existing = result.scalars().first()

            if existing:
                existing.readed_at = datetime.now(timezone.utc)
                session.add(existing)
            else:
                reader = AnnouncementReader(
                    announcement_id=announcement_id,
                    user_id=user_id
                )
                session.add(reader)

            session.commit()
            return True

    @staticmethod
    def get_read_count(announcement_id: UUID) -> int:
        """获取公告已读人数"""
        with db_config.get_session() as session:
            query = select(AnnouncementReader).where(AnnouncementReader.announcement_id == announcement_id)
            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def is_read(announcement_id: UUID, user_id: UUID) -> bool:
        """检查用户是否已读公告"""
        with db_config.get_session() as session:
            query = select(AnnouncementReader).where(
                AnnouncementReader.announcement_id == announcement_id,
                AnnouncementReader.user_id == user_id
            )
            result = session.execute(query)
            return result.scalars().first() is not None

    @staticmethod
    def get_readers(announcement_id: UUID, skip: int = 0, limit: int = 100) -> dict:
        """获取公告的已读用户列表"""
        with db_config.get_session() as session:
            query = (
                select(AnnouncementReader, User)
                .join(User, AnnouncementReader.user_id == User.user_id)
                .where(AnnouncementReader.announcement_id == announcement_id)
                .order_by(AnnouncementReader.readed_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = session.execute(query)
            readers = []
            for reader, user in result.all():
                readers.append({
                    "user_id": str(user.user_id),
                    "user_name": user.real_name,
                    "user_code": user.employee_id,
                    "readed_at": reader.readed_at.isoformat() if reader.readed_at else None
                })

            count_query = select(AnnouncementReader).where(AnnouncementReader.announcement_id == announcement_id)
            count_result = session.execute(count_query)
            total = len(list(count_result.scalars().all()))

            return {
                "total": total,
                "readers": readers
            }


class UserMessageService:
    """用户消息服务"""

    @staticmethod
    def create_message(send_user: UUID, receive_user: UUID, content: str) -> UserMessage:
        """创建用户消息"""
        with db_config.get_session() as session:
            message = UserMessage(
                send_user=send_user,
                receive_user=receive_user,
                content=content
            )
            
            if send_user == receive_user:
                message.status = "read"
                message.readed_at = datetime.now(timezone.utc)
            
            session.add(message)
            session.commit()
            session.refresh(message)
            msg_dict = {
                "message_id": str(message.msg_id),
                "send_user": str(message.send_user),
                "receive_user": str(message.receive_user),
                "content": message.content,
                "status": message.status,
                "created_at": message.created_at.isoformat() if message.created_at else None
            }
            SSEPushManager.push_message_sync(
                receive_user,
                "user_message",
                msg_dict
            )
            return message

    @staticmethod
    def get_user_sent_messages(user_id: UUID, skip: int = 0, limit: int = 100) -> List[UserMessage]:
        """获取用户发送的消息"""
        with db_config.get_session() as session:
            query = select(UserMessage).where(
                UserMessage.send_user == user_id
            ).order_by(UserMessage.created_at.desc()).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def get_user_received_messages(user_id: UUID, skip: int = 0, limit: int = 100) -> List[UserMessage]:
        """获取用户接收的消息"""
        with db_config.get_session() as session:
            query = select(UserMessage).where(
                UserMessage.receive_user == user_id
            ).order_by(UserMessage.created_at.desc()).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_user_messages(user_id: UUID, status: Optional[str] = None, is_sent: bool = False) -> int:
        """统计用户消息数量"""
        with db_config.get_session() as session:
            if is_sent:
                query = select(UserMessage).where(UserMessage.send_user == user_id)
            else:
                query = select(UserMessage).where(UserMessage.receive_user == user_id)

            if status:
                query = query.where(UserMessage.status == status)

            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def get_message_by_id(msg_id: UUID) -> Optional[UserMessage]:
        """根据ID获取消息"""
        with db_config.get_session() as session:
            return session.get(UserMessage, msg_id)

    @staticmethod
    def mark_as_read(msg_id: UUID) -> bool:
        """标记消息为已读"""
        with db_config.get_session() as session:
            message = session.get(UserMessage, msg_id)
            if not message:
                return False
            message.status = "read"
            message.readed_at = datetime.now(timezone.utc)
            session.add(message)
            session.commit()
            return True

    @staticmethod
    def mark_all_received_as_read(user_id: UUID) -> int:
        """标记用户所有接收消息为已读"""
        with db_config.get_session() as session:
            query = select(UserMessage).where(
                UserMessage.receive_user == user_id,
                UserMessage.status == "unread"
            )
            result = session.execute(query)
            messages = list(result.scalars().all())
            for message in messages:
                message.status = "read"
                message.readed_at = datetime.now(timezone.utc)
                session.add(message)
            session.commit()
            return len(messages)

    @staticmethod
    def delete_message(msg_id: UUID) -> bool:
        """删除消息"""
        with db_config.get_session() as session:
            message = session.get(UserMessage, msg_id)
            if not message:
                return False
            session.delete(message)
            session.commit()
            return True


# 全局服务实例
system_message_service = SystemMessageService()
announcement_service = AnnouncementService()
user_message_service = UserMessageService()
