from datetime import date, datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, JSON
from sqlalchemy import Column


class ProductionLine(SQLModel, table=True):
    """生产线表

    用于管理生产线上的设备分组, 支持多层级的生产线组织结构.
    """
    __tablename__ = "production_lines"

    production_line_id: UUID = Field(primary_key=True, default_factory=uuid4, description="生产线ID, UUID格式")
    production_line_manager: Optional[UUID] = Field(default=None, foreign_key="users.user_id", description="生产线负责人ID, 允许为空")
    production_line_loc: str = Field(nullable=False, description="生产线位置")
    production_line_name: str = Field(nullable=False, description="生产线名称")

    devices: List["Device"] = Relationship(back_populates="production_line")


class DeviceApproval(SQLModel, table=True):
    """设备审批表
    
    记录设备的审批流程信息, 包括审批发起人和审批人. 
    """
    __tablename__ = "device_approvals"
    
    device_approval_id: UUID = Field(primary_key=True, default_factory=uuid4, description="审批记录ID, UUID格式")
    approval_send: UUID = Field(nullable=False, foreign_key="users.user_id", description="审批发起人ID")
    approval_by: UUID = Field(nullable=False, foreign_key="users.user_id", description="审批人ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="审批创建时间")    
    processed_at: Optional[datetime] = Field(default=None, description="审批处理时间")
    approval_status: str = Field(default="pending", description="审批状态: pending(待审批), approved(已通过), rejected(已拒绝)")
    
    devices: List["Device"] = Relationship(back_populates="device_approval")
    
    sender: "User" = Relationship(back_populates="approvals_sent", sa_relationship_kwargs={"foreign_keys": "DeviceApproval.approval_send"})
    approver: "User" = Relationship(back_populates="approvals_received", sa_relationship_kwargs={"foreign_keys": "DeviceApproval.approval_by"})


class Device(SQLModel, table=True):
    """设备表
    
    记录所有设备的基本信息, 包括设备类型, 所属生产线, 负责人等. 
    """
    __tablename__ = "devices"
    
    device_id: UUID = Field(primary_key=True, default_factory=uuid4, description="设备ID, UUID格式")
    device_name: str = Field(nullable=False, description="设备名称")
    device_type: str = Field(nullable=False, description="设备类型")
    device_upload_token: Optional[str] = Field(default=None, description="设备上传Token")
    production_line_id: UUID = Field(nullable=False, foreign_key="production_lines.production_line_id", description="所属生产线ID")
    device_manager: UUID = Field(nullable=False, foreign_key="users.user_id", description="设备负责人ID")
    ip_addr: Optional[str] = Field(default=None, description="设备IP地址")
    mac_addr: Optional[str] = Field(default=None, description="设备MAC地址")
    status: str = Field(default="inactive", description="设备状态: inactive(未激活), active(运行中), maintenance(维护中), fault(故障), removed(已移除)")
    device_approval_id: Optional[UUID] = Field(default=None, foreign_key="device_approvals.device_approval_id", description="关联的审批记录ID")
    installation_date: Optional[date] = Field(default=None, description="设备安装日期")
    
    production_line: ProductionLine = Relationship(back_populates="devices")
    manager: "User" = Relationship(back_populates="managed_devices")
    device_approval: Optional[DeviceApproval] = Relationship(back_populates="devices")
    status_history: List["DeviceStatusHistory"] = Relationship(back_populates="device")
    detection_records: List["DetectionRecord"] = Relationship(back_populates="device")


class DeviceStatusHistory(SQLModel, table=True):
    """设备历史状态表(时序数据)
    
    记录设备状态的历史变化, 用于设备监控和性能分析. 
    """
    __tablename__ = "device_status_history"
    
    history_id: UUID = Field(primary_key=True, default_factory=uuid4, description="记录ID, UUID格式")
    device_id: UUID = Field(nullable=False, foreign_key="devices.device_id", description="设备ID")
    status: str = Field(nullable=False, description="设备状态")
    cpu_usage: Optional[float] = Field(default=None, description="CPU使用率(0-100)")
    memory_usage: Optional[float] = Field(default=None, description="内存使用率(0-100)")
    network_latency: Optional[int] = Field(default=None, description="网络延迟(ms)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="记录创建时间")
    
    device: Device = Relationship(back_populates="status_history")


class DefectType(SQLModel, table=True):
    """缺陷类型表
    
    定义检测系统中识别的缺陷类型, 用于统一缺陷分类. 
    """
    __tablename__ = "defect_types"
    
    defect_type_id: int = Field(primary_key=True, description="缺陷类型ID")
    defect_type_name: str = Field(max_length=50, nullable=False, description="缺陷类型名称")


class DetectionRecord(SQLModel, table=True):
    """检测记录表
    
    每个设备每time gap间隔内使用一条记录, 时间间隔内第一次创建, 后续都是更新. 
    记录格式: 'BTH[year][month][day][hour][min // time gap + 1]'
    """
    __tablename__ = "detection_records"
    
    record_batch_id: str = Field(primary_key=True, description="检测批次ID, 格式: BTH[year][month][day][hour][min//time_gap+1]")
    device_id: UUID = Field(nullable=False, foreign_key="devices.device_id", description="设备ID")
    detect_count: Optional[int] = Field(default=None, description="检测总数")
    pass_count: Optional[int] = Field(default=None, description="通过数量")
    detect_info: List = Field(sa_column=Column(JSON, nullable=False), description="检测信息JSON数组, 格式: [{'defect_type_id': ?, 'defect_count': ?}, ...], 无缺陷时为[]")
    latest_upload_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后更新时间")
    
    device: Device = Relationship(back_populates="detection_records")
    defect_details: List["DefectDetail"] = Relationship(back_populates="detection_record")


class DefectDetail(SQLModel, table=True):
    """缺陷细节表
    
    检测出缺陷后记录对应照片和缺陷详情. 
    """
    __tablename__ = "defect_details"
    
    defect_details_id: UUID = Field(primary_key=True, default_factory=uuid4, description="缺陷详情ID, UUID格式")
    record_batch_id: str = Field(nullable=False, foreign_key="detection_records.record_batch_id", description="关联的检测批次ID")
    original_img: str = Field(max_length=500, nullable=False, description="原始图片URL")
    defect_count: Optional[int] = Field(default=None, description="缺陷数量")
    details: Optional[List] = Field(sa_column=Column(JSON), description="缺陷详情JSON数组, 格式: [{'defect_type_id': ?, 'xyhw': (?,?,?,?), 'conf':?}, ...]")
    
    detection_record: DetectionRecord = Relationship(back_populates="defect_details")
    review_tasks: List["ReviewTask"] = Relationship(back_populates="defect_detail")


class ReviewTask(SQLModel, table=True):
    """人工审查表
    
    记录人工审查缺陷的任务信息, 包括审查状态和审查结果. 
    """
    __tablename__ = "review_tasks"
    
    review_task_id: UUID = Field(primary_key=True, default_factory=uuid4, description="审查任务ID, UUID格式")
    defect_details_id: UUID = Field(nullable=False, foreign_key="defect_details.defect_details_id", description="关联的缺陷详情ID")
    assignee_id: UUID = Field(nullable=False, foreign_key="users.user_id", description="被分配任务的质检员ID")
    reviewer_id: Optional[UUID] = Field(default=None, foreign_key="users.user_id", description="实际审查的员工ID, 允许为空")
    review_status: str = Field(max_length=20, default="pending", description="审查状态: pending(待审查), completed(已完成), cancel(已取消), timeout(已超时)")
    review_result: Optional[str] = Field(max_length=20, default=None, description="审查结果: confirmed(确认缺陷), false_positive(误报), uncertain(不确定), confusion(混淆)")
    review_defect_count: Optional[int] = Field(default=None, description="审查确认的缺陷数量")
    has_details: Optional[bool] = Field(default=None, description="是否有细节更改, 未检查为NULL, 无细节改变则false且review_details为NULL")
    review_details: Optional[List] = Field(sa_column=Column(JSON), description="审查后的缺陷详情, 格式: [{'defect_type_id': ?, 'xyhw': (?,?,?,?), 'conf':?}, ...]")
    review_comment: Optional[str] = Field(default=None, description="审查备注")
    assignee_at: Optional[datetime] = Field(default=None, description="任务分配时间")
    completed_at: Optional[datetime] = Field(default=None, description="任务完成时间")
    
    defect_detail: DefectDetail = Relationship(back_populates="review_tasks")
    assignee: "User" = Relationship(back_populates="assigned_tasks", sa_relationship_kwargs={"foreign_keys": "ReviewTask.assignee_id"})
    reviewer: Optional["User"] = Relationship(back_populates="reviewed_tasks", sa_relationship_kwargs={"foreign_keys": "ReviewTask.reviewer_id"})


class Role(SQLModel, table=True):
    """角色表
    
    角色决定用户权限, 系统角色不允许修改. 
    """
    __tablename__ = "roles"
    
    role_id: int = Field(primary_key=True, description="角色ID")
    role_name: str = Field(max_length=30, unique=True, nullable=False, description="角色名称")
    desc: Optional[str] = Field(default=None, description="角色描述")
    is_system_role: bool = Field(default=False, description="是否为系统角色")
    permissions: Optional[dict[str, str]] = Field(sa_column=Column(JSON), description="权限列表, 格式: [{'api': ?, 'accessibility': ?}, ...]")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    
    users: List["User"] = Relationship(back_populates="role")


class Department(SQLModel, table=True):
    """部门表
    
    支持层级结构的部门组织, 顶级部门parent_id为NULL. 
    """
    __tablename__ = "departments"
    
    department_id: int = Field(primary_key=True, description="部门ID")
    department_code: str = Field(max_length=30, unique=True, nullable=False, description="部门编码")
    department_name: str = Field(max_length=100, nullable=False, description="部门名称")
    parent_id: Optional[int] = Field(default=None, foreign_key="departments.department_id", description="上级部门ID, 顶级部门为NULL")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    
    users: List["User"] = Relationship(back_populates="department")


class Title(SQLModel, table=True):
    """职称表
    
    定义员工的职称信息. 
    """
    __tablename__ = "titles"
    
    title_id: int = Field(primary_key=True, description="职称ID")
    title_name: str = Field(max_length=30, nullable=False, description="职称名称")
    
    users: List["User"] = Relationship(back_populates="title")


class User(SQLModel, table=True):
    """用户表
    
    记录系统用户的基本信息, 包括认证信息和关联关系. 
    """
    __tablename__ = "users"
    
    user_id: UUID = Field(primary_key=True, default_factory=uuid4, description="用户ID, UUID格式")
    user_name: str = Field(max_length=50, nullable=False, description="用户名")
    password_hash: str = Field(max_length=255, nullable=False, description="密码哈希值, 使用bcrypt加盐")
    employee_id: Optional[str] = Field(max_length=20, unique=True, default=None, description="工号")
    real_name: str = Field(max_length=50, nullable=False, description="真实姓名")
    email: Optional[str] = Field(max_length=100, default=None, description="邮箱")
    phone: Optional[str] = Field(max_length=20, default=None, description="联系电话")
    department_id: Optional[int] = Field(default=None, foreign_key="departments.department_id", description="所属部门ID")
    title_id: int = Field(nullable=False, foreign_key="titles.title_id", description="职称ID")
    avatar_url: Optional[str] = Field(max_length=500, default=None, description="头像URL")
    role_id: int = Field(nullable=False, foreign_key="roles.role_id", description="角色ID")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    
    role: Role = Relationship(back_populates="users")
    department: Optional[Department] = Relationship(back_populates="users")
    title: Title = Relationship(back_populates="users")
    managed_devices: List[Device] = Relationship(back_populates="manager")
    approvals_sent: List[DeviceApproval] = Relationship(back_populates="sender", sa_relationship_kwargs={"foreign_keys": "DeviceApproval.approval_send"})
    approvals_received: List[DeviceApproval] = Relationship(back_populates="approver", sa_relationship_kwargs={"foreign_keys": "DeviceApproval.approval_by"})
    assigned_tasks: List[ReviewTask] = Relationship(back_populates="assignee", sa_relationship_kwargs={"foreign_keys": "ReviewTask.assignee_id"})
    reviewed_tasks: List[ReviewTask] = Relationship(back_populates="reviewer", sa_relationship_kwargs={"foreign_keys": "ReviewTask.reviewer_id"})
    operation_logs: List["UserOperationLog"] = Relationship(back_populates="user")
    messages_sent: List["UserMessage"] = Relationship(back_populates="sender", sa_relationship_kwargs={"foreign_keys": "UserMessage.send_user"})
    messages_received: List["UserMessage"] = Relationship(back_populates="receiver", sa_relationship_kwargs={"foreign_keys": "UserMessage.receive_user"})
    system_messages: List["SystemMessage"] = Relationship(back_populates="receiver")
    announcements: List["Announcement"] = Relationship(back_populates="sender")
    announcement_reads: List["AnnouncementReader"] = Relationship(back_populates="user")


class UserOperationLog(SQLModel, table=True):
    """用户操作日志表
    
    记录用户的所有操作行为, 用于审计和追溯. 
    """
    __tablename__ = "user_operation_logs"
    
    log_id: UUID = Field(primary_key=True, default_factory=uuid4, description="日志ID, UUID格式")
    user_id: UUID = Field(nullable=False, foreign_key="users.user_id", description="操作用户ID")
    operation_type: str = Field(max_length=50, nullable=False, description="操作类型")
    operation_details: Optional[str] = Field(default=None, description="操作详情")
    ip_addr: Optional[str] = Field(default=None, description="操作IP地址")
    operation_result: str = Field(max_length=20, default="success", description="操作结果: success(成功), fail(失败)")
    error_msg: Optional[str] = Field(default=None, description="错误信息")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="操作时间")
    
    user: User = Relationship(back_populates="operation_logs")


class UserMessage(SQLModel, table=True):
    """用户消息表
    
    记录用户之间的消息通信. 
    """
    __tablename__ = "user_messages"
    
    msg_id: UUID = Field(primary_key=True, default_factory=uuid4, description="消息ID, UUID格式")
    send_user: UUID = Field(nullable=False, foreign_key="users.user_id", description="发送用户ID")
    receive_user: UUID = Field(nullable=False, foreign_key="users.user_id", description="接收用户ID")
    content: str = Field(nullable=False, description="消息内容")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="发送时间")
    status: str = Field(max_length=20, default="unread", description="消息状态: read(已读), unread(未读)")
    readed_at: Optional[datetime] = Field(default=None, description="阅读时间")
    
    sender: User = Relationship(back_populates="messages_sent", sa_relationship_kwargs={"foreign_keys": "UserMessage.send_user"})
    receiver: User = Relationship(back_populates="messages_received", sa_relationship_kwargs={"foreign_keys": "UserMessage.receive_user"})


class SystemMessage(SQLModel, table=True):
    """系统消息表
    
    记录系统向用户发送的通知消息.
    """
    __tablename__ = "system_messages"
    
    msg_id: UUID = Field(primary_key=True, default_factory=uuid4, description="消息ID, UUID格式")
    receive_user: UUID = Field(nullable=False, foreign_key="users.user_id", description="接收用户ID")
    content: str = Field(nullable=False, description="消息内容")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="发送时间")
    status: str = Field(max_length=20, default="unread", description="消息状态: read(已读), unread(未读)")
    readed_at: Optional[datetime] = Field(default=None, description="阅读时间")
    
    receiver: User = Relationship(back_populates="system_messages")


class Announcement(SQLModel, table=True):
    """公告表
    
    记录系统发布的公告信息,支持按部门/角色/职称定向发布.
    """
    __tablename__ = "announcements"
    
    announcement_id: UUID = Field(primary_key=True, default_factory=uuid4, description="公告ID, UUID格式")
    receiver_type: str = Field(max_length=20, default="all", description="接收类型: all(全部), department(部门), role(角色), title(职称)")
    receive_target: Optional[int] = Field(default=None, description="接收目标ID, all时为NULL")
    content: str = Field(nullable=False, description="公告内容")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="发布时间")
    send_user: UUID = Field(nullable=False, foreign_key="users.user_id", description="发布用户ID")
    expired: datetime = Field(nullable=False, description="过期时间")
    
    sender: User = Relationship(back_populates="announcements")
    readers: List["AnnouncementReader"] = Relationship(back_populates="announcement")


class AnnouncementReader(SQLModel, table=True):
    """公告已读表
    
    记录用户阅读公告的情况.
    """
    __tablename__ = "announcement_readers"
    
    announcement_id: UUID = Field(primary_key=True, foreign_key="announcements.announcement_id", description="公告ID")
    user_id: UUID = Field(primary_key=True, foreign_key="users.user_id", description="用户ID")
    readed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="阅读时间")
    
    announcement: Announcement = Relationship(back_populates="readers")
    user: User = Relationship(back_populates="announcement_reads")
