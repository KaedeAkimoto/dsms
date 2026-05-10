from datetime import date, datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, or_

from app.config.database import db_config
from app.models.models import Device, ProductionLine, DeviceApproval, DeviceStatusHistory


class DeviceService:
    @staticmethod
    def create_device(
        device_name: str,
        device_type: str,
        production_line_id: UUID,
        device_manager: UUID,
        ip_addr: Optional[str] = None,
        mac_addr: Optional[str] = None,
        installation_date: Optional[date] = None
    ) -> Optional[Device]:
        with db_config.get_session() as session:
            device = Device(
                device_id=uuid4(),
                device_name=device_name,
                device_type=device_type,
                production_line_id=production_line_id,
                device_manager=device_manager,
                ip_addr=ip_addr,
                mac_addr=mac_addr,
                installation_date=installation_date,
                status="inactive"
            )
            session.add(device)
            session.commit()
            session.refresh(device)
            return device

    @staticmethod
    def get_device_by_id(device_id: UUID) -> Optional[Device]:
        with db_config.get_session() as session:
            device = session.get(Device, device_id)
            if device:
                session.refresh(device)
            return device

    @staticmethod
    def get_all_devices(skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Device]:
        with db_config.get_session() as session:
            query = select(Device)
            if status:
                query = query.where(Device.status == status)
            else:
                query = query.where(Device.status != "removed")
            query = query.offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_devices(status: Optional[str] = None) -> int:
        with db_config.get_session() as session:
            query = select(func.count(Device.device_id))
            if status:
                query = query.where(Device.status == status)
            else:
                query = query.where(Device.status != "removed")
            result = session.execute(query)
            return result.scalar() or 0

    @staticmethod
    def update_device(device_id: UUID, **kwargs) -> Optional[Device]:
        with db_config.get_session() as session:
            device = session.get(Device, device_id)
            if not device:
                return None

            for key, value in kwargs.items():
                if value is not None and hasattr(device, key):
                    setattr(device, key, value)

            session.add(device)
            session.commit()
            session.refresh(device)
            return device

    @staticmethod
    def delete_device(device_id: UUID) -> bool:
        with db_config.get_session() as session:
            device = session.get(Device, device_id)
            if not device:
                return False
            device.status = "removed"
            session.add(device)
            session.commit()
            return True

    @staticmethod
    def generate_upload_token(device_id: UUID) -> Optional[Device]:
        import secrets
        with db_config.get_session() as session:
            device = session.get(Device, device_id)
            if not device:
                return None
            if device.device_upload_token:
                session.refresh(device)
                return device
            token = secrets.token_urlsafe(32)
            device.device_upload_token = token
            session.add(device)
            session.commit()
            session.refresh(device)
            return device

    @staticmethod
    def get_device_with_token(device_id: UUID) -> Optional[dict]:
        with db_config.get_session() as session:
            device = session.get(Device, device_id)
            if not device:
                return None
            return {
                "device_id": str(device.device_id),
                "device_name": device.device_name,
                "device_upload_token": device.device_upload_token
            }

    @staticmethod
    def get_all_devices_with_tokens() -> List[dict]:
        with db_config.get_session() as session:
            query = select(Device).where(Device.device_upload_token.isnot(None))
            result = session.execute(query)
            devices = result.scalars().all()
            return [
                {
                    "device_id": str(d.device_id),
                    "device_name": d.device_name,
                    "device_upload_token": d.device_upload_token
                }
                for d in devices
            ]

    @staticmethod
    def batch_generate_upload_tokens(device_ids: List[UUID]) -> List[dict]:
        import secrets
        with db_config.get_session() as session:
            results = []
            for device_id in device_ids:
                device = session.get(Device, device_id)
                if device:
                    token = secrets.token_urlsafe(32)
                    device.device_upload_token = token
                    session.add(device)
                    results.append({
                        "device_id": str(device_id),
                        "device_name": device.device_name,
                        "device_upload_token": token
                    })
            session.commit()
            return results

    @staticmethod
    def get_devices_by_production_line(production_line_id: UUID, skip: int = 0, limit: int = 100) -> List[Device]:
        """根据生产线ID获取设备列表"""
        with db_config.get_session() as session:
            query = select(Device).where(
                Device.production_line_id == production_line_id,
                Device.status != "removed"
            ).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_devices_by_production_line(production_line_id: UUID) -> int:
        """统计生产线设备数量"""
        with db_config.get_session() as session:
            query = select(func.count(Device.device_id)).where(
                Device.production_line_id == production_line_id,
                Device.status != "removed"
            )
            result = session.execute(query)
            return result.scalar() or 0

    @staticmethod
    def get_devices_by_type(device_type: str, skip: int = 0, limit: int = 100) -> List[Device]:
        """根据设备类型获取设备列表"""
        with db_config.get_session() as session:
            query = select(Device).where(
                Device.device_type == device_type,
                Device.status != "removed"
            ).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_devices_by_type(device_type: str) -> int:
        """统计设备类型数量"""
        with db_config.get_session() as session:
            query = select(func.count(Device.device_id)).where(
                Device.device_type == device_type,
                Device.status != "removed"
            )
            result = session.execute(query)
            return result.scalar() or 0

    @staticmethod
    def search_devices(keyword: str, skip: int = 0, limit: int = 100) -> List[Device]:
        """按设备名称模糊搜索设备"""
        with db_config.get_session() as session:
            query = select(Device).where(
                Device.device_name.like(f"%{keyword}%"),
                Device.status != "removed"
            ).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_search_devices(keyword: str) -> int:
        """统计搜索结果数量"""
        with db_config.get_session() as session:
            query = select(func.count(Device.device_id)).where(
                Device.device_name.like(f"%{keyword}%"),
                Device.status != "removed"
            )
            result = session.execute(query)
            return result.scalar() or 0

    @staticmethod
    def get_device_status_stats() -> dict:
        """获取设备状态统计"""
        with db_config.get_session() as session:
            total = session.execute(select(func.count(Device.device_id))).scalar() or 0
            
            online = session.execute(
                select(func.count(Device.device_id)).where(Device.status == "online")
            ).scalar() or 0
            
            offline = session.execute(
                select(func.count(Device.device_id)).where(Device.status == "offline")
            ).scalar() or 0
            
            inactive = session.execute(
                select(func.count(Device.device_id)).where(Device.status == "inactive")
            ).scalar() or 0
            
            removed = session.execute(
                select(func.count(Device.device_id)).where(Device.status == "removed")
            ).scalar() or 0

            return {
                "total": total,
                "online": online,
                "offline": offline,
                "inactive": inactive,
                "removed": removed
            }


class ProductionLineService:
    @staticmethod
    def create_production_line(
        production_line_name: str,
        production_line_loc: str,
        production_line_manager: Optional[UUID] = None
    ) -> Optional[ProductionLine]:
        with db_config.get_session() as session:
            line = ProductionLine(
                production_line_id=uuid4(),
                production_line_name=production_line_name,
                production_line_loc=production_line_loc,
                production_line_manager=production_line_manager
            )
            session.add(line)
            session.commit()
            session.refresh(line)
            return line

    @staticmethod
    def get_production_line_by_id(production_line_id: UUID) -> Optional[ProductionLine]:
        with db_config.get_session() as session:
            line = session.get(ProductionLine, production_line_id)
            if line:
                session.refresh(line)
            return line

    @staticmethod
    def get_all_production_lines(skip: int = 0, limit: int = 100) -> List[ProductionLine]:
        with db_config.get_session() as session:
            query = select(ProductionLine).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_production_lines() -> int:
        with db_config.get_session() as session:
            query = select(ProductionLine)
            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def search_production_lines(keyword: str, skip: int = 0, limit: int = 100) -> List[ProductionLine]:
        with db_config.get_session() as session:
            query = (
                select(ProductionLine)
                .where(
                    or_(
                        ProductionLine.production_line_name.ilike(f"%{keyword}%"),
                        ProductionLine.production_line_loc.ilike(f"%{keyword}%")
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_search_production_lines(keyword: str) -> int:
        with db_config.get_session() as session:
            query = (
                select(ProductionLine)
                .where(
                    or_(
                        ProductionLine.production_line_name.ilike(f"%{keyword}%"),
                        ProductionLine.production_line_loc.ilike(f"%{keyword}%")
                    )
                )
            )
            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def update_production_line(production_line_id: UUID, **kwargs) -> Optional[ProductionLine]:
        with db_config.get_session() as session:
            line = session.get(ProductionLine, production_line_id)
            if not line:
                return None

            for key, value in kwargs.items():
                if value is not None and hasattr(line, key):
                    setattr(line, key, value)

            session.add(line)
            session.commit()
            session.refresh(line)
            return line

    @staticmethod
    def delete_production_line(production_line_id: UUID) -> bool:
        with db_config.get_session() as session:
            line = session.get(ProductionLine, production_line_id)
            if not line:
                return False
            session.delete(line)
            session.commit()
            return True


class DeviceApprovalService:
    @staticmethod
    def create_approval(
        approval_send: UUID,
        approval_by: UUID,
        device_id: Optional[UUID] = None
    ) -> Optional[DeviceApproval]:
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        
        with db_config.get_session() as session:
            approval = DeviceApproval(
                device_approval_id=uuid4(),
                approval_send=approval_send,
                approval_by=approval_by,
                approval_status="pending"
            )
            session.add(approval)
            session.commit()
            session.refresh(approval)
            
            # 如果提供了设备ID，关联设备和审批
            if device_id:
                device = session.get(Device, device_id)
                if device:
                    device.device_approval_id = approval.device_approval_id
                    session.commit()
            
            # 重新查询并预加载设备关系，确保返回的对象可以访问devices
            result = session.execute(
                select(DeviceApproval)
                .options(joinedload(DeviceApproval.devices))
                .where(DeviceApproval.device_approval_id == approval.device_approval_id)
            )
            return result.scalars().first()

    @staticmethod
    def get_approval_by_id(device_approval_id: UUID) -> Optional[DeviceApproval]:
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        
        with db_config.get_session() as session:
            result = session.execute(
                select(DeviceApproval)
                .options(joinedload(DeviceApproval.devices))
                .where(DeviceApproval.device_approval_id == device_approval_id)
            )
            return result.scalars().first()

    @staticmethod
    def get_all_approvals(skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[DeviceApproval]:
        from sqlalchemy.orm import joinedload
        
        with db_config.get_session() as session:
            query = select(DeviceApproval).options(joinedload(DeviceApproval.devices))
            if status:
                query = query.where(DeviceApproval.approval_status == status)
            query = query.offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().unique().all())

    @staticmethod
    def count_approvals(status: Optional[str] = None) -> int:
        with db_config.get_session() as session:
            query = select(DeviceApproval)
            if status:
                query = query.where(DeviceApproval.approval_status == status)
            result = session.execute(query)
            return len(list(result.scalars().all()))

    @staticmethod
    def process_approval(device_approval_id: UUID, approved: bool) -> Optional[DeviceApproval]:
        with db_config.get_session() as session:
            approval = session.get(DeviceApproval, device_approval_id)
            if not approval:
                return None

            approval.approval_status = "approved" if approved else "rejected"
            approval.processed_at = datetime.now(timezone.utc)

            session.add(approval)
            session.commit()
            session.refresh(approval)
            return approval


class DeviceStatusHistoryService:
    @staticmethod
    def create_status_history(
        device_id: UUID,
        status: str,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        network_latency: Optional[int] = None
    ) -> Optional[DeviceStatusHistory]:
        with db_config.get_session() as session:
            history = DeviceStatusHistory(
                history_id=uuid4(),
                device_id=device_id,
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                network_latency=network_latency
            )
            session.add(history)
            session.commit()
            session.refresh(history)
            return history

    @staticmethod
    def get_device_history(
        device_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DeviceStatusHistory]:
        with db_config.get_session() as session:
            query = select(DeviceStatusHistory).where(
                DeviceStatusHistory.device_id == device_id
            ).offset(skip).limit(limit)
            result = session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    def count_device_history(device_id: UUID) -> int:
        with db_config.get_session() as session:
            query = select(DeviceStatusHistory).where(
                DeviceStatusHistory.device_id == device_id
            )
            result = session.execute(query)
            return len(list(result.scalars().all()))


device_service = DeviceService()
production_line_service = ProductionLineService()
device_approval_service = DeviceApprovalService()
device_status_history_service = DeviceStatusHistoryService()
