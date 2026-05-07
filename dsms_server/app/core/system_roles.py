from enum import Enum
from typing import List, Dict, Optional, Callable
from functools import wraps


class SystemRoleEnum(str, Enum):
    """系统角色枚举"""
    NO_PERMISSION_USER = "no_permission_user"   # 无权限用户（刚注册/离职）
    NORMAL_EMPLOYEE = "normal_employee"        # 普通员工
    DEVICE_ADMIN = "device_admin"              # 设备管理员
    DETECTION_MONITOR = "detection_monitor"    # 检测监控员
    HR_ADMIN = "hr_admin"                     # 人事管理员
    SENIOR_SYS_ADMIN = "senior_sys_admin"      # 高级系统管理员
    SUPER_SYS_ADMIN = "super_sys_admin"        # 超级系统管理员


class SystemRole:
    """系统角色定义"""

    NO_PERMISSION_USER = "no_permission_user"
    NORMAL_EMPLOYEE = "normal_employee"
    DEVICE_ADMIN = "device_admin"
    DETECTION_MONITOR = "detection_monitor"
    HR_ADMIN = "hr_admin"
    SENIOR_SYS_ADMIN = "senior_sys_admin"
    SUPER_SYS_ADMIN = "super_sys_admin"

    ALL_ROLES = [
        NO_PERMISSION_USER,
        NORMAL_EMPLOYEE,
        DEVICE_ADMIN,
        DETECTION_MONITOR,
        HR_ADMIN,
        SENIOR_SYS_ADMIN,
        SUPER_SYS_ADMIN,
    ]

    ROLE_NAMES = {
        NO_PERMISSION_USER: "无权限用户",
        NORMAL_EMPLOYEE: "普通员工",
        DEVICE_ADMIN: "设备管理员",
        DETECTION_MONITOR: "质检监控员",
        HR_ADMIN: "人事管理员",
        SENIOR_SYS_ADMIN: "系统管理员",
        SUPER_SYS_ADMIN: "超级系统管理员",
    }

    ROLE_DESCRIPTIONS = {
        NO_PERMISSION_USER: "刚注册或离职的用户，无任何系统权限，仅能访问登录相关接口",
        NORMAL_EMPLOYEE: "普通员工，可接收和发送消息，查看和确认公告，以及查看部分系统信息",
        DEVICE_ADMIN: "负责设备的添加、审批、状态监控等管理操作，以及生产线管理",
        DETECTION_MONITOR: "负责监控检测记录、缺陷详情、人工审查等检测相关操作",
        HR_ADMIN: "负责人事管理、部门管理、职称管理等人力资源操作",
        SENIOR_SYS_ADMIN: "负责系统配置、角色权限管理、审计日志查看等系统管理操作",
        SUPER_SYS_ADMIN: "拥有系统最高权限，可进行所有操作",
    }


class API:
    """API 定义类，用于注册 API 信息"""

    _apis: Dict[str, List[Dict]] = {}
    _api_methods: Dict[str, Dict] = {}

    def __init__(
        self,
        path: str,
        method: str = "GET",
        name: str = None,
        description: str = None,
        tags: List[str] = None,
        requires_auth: bool = True,
        required_roles: List[str] = None
    ):
        self.path = path
        self.method = method.upper()
        self.name = name or f"{method.upper()} {path}"
        self.description = description or ""
        self.tags = tags or []
        self.requires_auth = requires_auth
        self.required_roles = required_roles or []

    def to_permission(self) -> Dict[str, str]:
        """转换为权限格式"""
        return {
            "api": self.path,
            "accessibility": self.method
        }


class APIMeta(type):
    """API 注册器元类"""

    _registry: Dict[str, API] = {}

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # 自动注册带有 @api 装饰器的方法
        if hasattr(cls, '_api_methods'):
            for method_name, api_info in cls._api_methods.items():
                mcs._registry[f"{api_info.method}:{api_info.path}"] = api_info

        return cls


class APIRegistry(metaclass=APIMeta):
    """API 注册基类

    所有 API 路由类应继承此类，
    使用 @api 装饰器注册 API 信息。

    Usage:
        class UserAPI(APIRegistry):
            @api("/users", "GET", name="获取用户列表", tags=["用户管理"])
            async def get_users(...):
                ...

            @api("/users/{user_id}", "GET", name="获取用户详情", tags=["用户管理"])
            async def get_user(...):
                ...

        # 获取所有注册的 API
        APIRegistry.get_all_apis()
    """

    _api_methods: Dict[str, API] = {}
    _registry: Dict[str, API] = {}

    @classmethod
    def get_all_apis(cls) -> List[Dict]:
        """获取所有注册的 API"""
        apis = []
        for key, api in cls._registry.items():
            apis.append({
                "path": api.path,
                "method": api.method,
                "name": api.name,
                "description": api.description,
                "tags": api.tags,
                "requires_auth": api.requires_auth,
                "required_roles": api.required_roles
            })
        return apis

    @classmethod
    def get_apis_by_tag(cls, tag: str) -> List[Dict]:
        """按标签获取 API"""
        return [
            api for api in cls.get_all_apis()
            if tag in api["tags"]
        ]

    @classmethod
    def get_all_tags(cls) -> List[str]:
        """获取所有标签"""
        tags = set()
        for api in cls.get_all_apis():
            tags.update(api["tags"])
        return list(tags)

    @classmethod
    def clear_registry(cls):
        """清空注册表（主要用于测试）"""
        cls._registry.clear()


def api(
    path: str,
    method: str = "GET",
    name: str = None,
    description: str = None,
    tags: List[str] = None,
    requires_auth: bool = True,
    required_roles: List[str] = None
):
    """API 注册装饰器

    Args:
        path: API 路径
        method: HTTP 方法
        name: API 名称
        description: API 描述
        tags: 标签列表
        requires_auth: 是否需要认证
        required_roles: 需要的角色列表

    Usage:
        class UserAPI(APIRegistry):
            @api("/users", "GET", name="获取用户列表", tags=["用户"])
            async def get_users(self, request: Request):
                ...

        # 或者用于独立函数
        @api("/users", "GET", name="获取用户列表", tags=["用户"])
        async def get_users(request: Request):
            ...
    """
    def decorator(func):
        api_info = API(
            path=path,
            method=method,
            name=name,
            description=description,
            tags=tags,
            requires_auth=requires_auth,
            required_roles=required_roles
        )

        # 存储到函数的属性中
        func._api_info = api_info

        # 立即注册到全局注册表
        key = f"{method.upper()}:{path}"
        APIRegistry._registry[key] = api_info

        # 尝试注册到类的 _api_methods（如果是类方法）
        if hasattr(func, '__self__'):
            cls = type(func.__self__)
            if hasattr(cls, '_api_methods'):
                cls._api_methods[key] = api_info

        return func
    return decorator


def get_default_permissions(role: str) -> List[Dict[str, str]]:
    """获取角色的默认权限

    Args:
        role: 角色标识

    Returns:
        权限列表

    权限矩阵说明:
        超级管理员: 拥有系统所有权限
        系统管理员: 用户/部门/职称/审计/系统管理全部权限，设备/检测/审查只读
        人事管理员: 用户/部门/职称管理全部权限
        设备管理员: 设备/生产线全部权限，检测数据只读
        质检监控员: 检测数据/审查任务全部权限，设备/生产线/用户只读
        普通员工: 消息收发、公告查看确认、部分只读权限
    """
    permissions = {
        # 无权限用户 - 刚注册或离职，无任何权限
        SystemRole.NO_PERMISSION_USER: [],

        # 普通员工 - 基础权限（消息、公告、只读）
        SystemRole.NORMAL_EMPLOYEE: [
            # 消息相关
            {"api": "/api/v1/user-messages/*", "accessibility": "*"},
            {"api": "/api/v1/system-messages/my", "accessibility": "GET"},
            {"api": "/api/v1/system-messages/{msg_id}", "accessibility": "GET"},
            {"api": "/api/v1/system-messages/{msg_id}/read", "accessibility": "PUT"},
            {"api": "/api/v1/system-messages/my/read-all", "accessibility": "PUT"},
            # 公告相关
            {"api": "/api/v1/announcements/my", "accessibility": "GET"},
            {"api": "/api/v1/announcements/{announcement_id}", "accessibility": "GET"},
            {"api": "/api/v1/announcements/{announcement_id}/read", "accessibility": "PUT"},
            # SSE连接
            {"api": "/api/v1/sse/connect", "accessibility": "GET"},
            # 只读权限
            {"api": "/api/v1/devices/*", "accessibility": "GET"},
            {"api": "/api/v1/production-lines/*", "accessibility": "GET"},
            {"api": "/api/v1/users/me", "accessibility": "GET"},
            {"api": "/api/v1/users/{user_id}", "accessibility": "GET"},
            {"api": "/api/v1/departments/*", "accessibility": "GET"},
            {"api": "/api/v1/titles/*", "accessibility": "GET"},
            {"api": "/api/v1/roles/*", "accessibility": "GET"},
            {"api": "/api/v1/common/*", "accessibility": "GET"},
            {"api": "/api/v1/auth/*", "accessibility": "GET"},
            {"api": "/api/v1/defect-types", "accessibility": "GET"},
        ],

        # 超级管理员 - 最高权限，可进行所有操作
        SystemRole.SUPER_SYS_ADMIN: [
            {"api": "*", "accessibility": "*"},
        ],

        # 系统管理员 - 运维管理（不含敏感权限）
        SystemRole.SENIOR_SYS_ADMIN: [
            {"api": "/api/v1/users/*", "accessibility": "*"},
            {"api": "/api/v1/roles/*", "accessibility": "GET"},
            {"api": "/api/v1/departments/*", "accessibility": "*"},
            {"api": "/api/v1/titles/*", "accessibility": "*"},
            {"api": "/api/v1/devices/*", "accessibility": "GET"},
            {"api": "/api/v1/production-lines/*", "accessibility": "GET"},
            {"api": "/api/v1/device-approvals/*", "accessibility": "GET"},
            {"api": "/api/v1/device-status-history/*", "accessibility": "GET"},
            {"api": "/api/v1/detection-records/*", "accessibility": "GET"},
            {"api": "/api/v1/defect-details/*", "accessibility": "GET"},
            {"api": "/api/v1/defect-types/*", "accessibility": "GET"},
            {"api": "/api/v1/review-tasks/*", "accessibility": "GET"},
            {"api": "/api/v1/audit-logs/*", "accessibility": "*"},
            {"api": "/api/v1/admin/*", "accessibility": "*"},
            {"api": "/api/v1/common/*", "accessibility": "GET"},
            {"api": "/api/v1/auth/*", "accessibility": "GET"},
        ],

        # 人事管理员 - HR（用户/部门/职称管理）
        SystemRole.HR_ADMIN: [
            {"api": "/api/v1/users/*", "accessibility": "*"},
            {"api": "/api/v1/departments/*", "accessibility": "*"},
            {"api": "/api/v1/titles/*", "accessibility": "*"},
            {"api": "/api/v1/roles/*", "accessibility": "GET"},
            {"api": "/api/v1/common/*", "accessibility": "GET"},
            {"api": "/api/v1/auth/*", "accessibility": "GET"},
        ],

        # 设备管理员 - 设备运维（设备/生产线全部权限）
        SystemRole.DEVICE_ADMIN: [
            {"api": "/api/v1/devices/*", "accessibility": "*"},
            {"api": "/api/v1/production-lines/*", "accessibility": "*"},
            {"api": "/api/v1/device-approvals/*", "accessibility": "*"},
            {"api": "/api/v1/device-status-history/*", "accessibility": "*"},
            {"api": "/api/v1/detection-records/*", "accessibility": "GET"},
            {"api": "/api/v1/defect-details/*", "accessibility": "GET"},
            {"api": "/api/v1/defect-types/*", "accessibility": "GET"},
            {"api": "/api/v1/users/*", "accessibility": "GET"},
            {"api": "/api/v1/common/*", "accessibility": "GET"},
            {"api": "/api/v1/auth/*", "accessibility": "GET"},
        ],

        # 质检监控员 - 质量控制（检测/审查全部权限）
        SystemRole.DETECTION_MONITOR: [
            {"api": "/api/v1/detection-records/*", "accessibility": "*"},
            {"api": "/api/v1/defect-details/*", "accessibility": "*"},
            {"api": "/api/v1/defect-types/*", "accessibility": "*"},
            {"api": "/api/v1/review-tasks/*", "accessibility": "*"},
            {"api": "/api/v1/devices/*", "accessibility": "GET"},
            {"api": "/api/v1/production-lines/*", "accessibility": "GET"},
            {"api": "/api/v1/device-approvals/*", "accessibility": "GET"},
            {"api": "/api/v1/device-status-history/*", "accessibility": "GET"},
            {"api": "/api/v1/users/*", "accessibility": "GET"},
            {"api": "/api/v1/common/*", "accessibility": "GET"},
            {"api": "/api/v1/auth/*", "accessibility": "GET"},
        ],
    }
    return permissions.get(role, [])


def get_all_system_roles() -> List[Dict]:
    """获取所有系统角色的定义"""
    roles = []
    for role_key in SystemRole.ALL_ROLES:
        roles.append({
            "role_key": role_key,
            "role_name": SystemRole.ROLE_NAMES.get(role_key, role_key),
            "description": SystemRole.ROLE_DESCRIPTIONS.get(role_key, ""),
            "is_system_role": True,
            "default_permissions": get_default_permissions(role_key)
        })
    return roles
