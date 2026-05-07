# DSMS API 接口文档

> 基于 FastAPI 构建的缺陷检测管理系统 RESTful API 文档
>
> **版本**: v1
>
> **基础路径**: `/api/v1`
>
> **请求超时**: 所有接口均设置请求超时（可在配置文件中 `server.request_timeout_seconds` 调整，默认 30 秒）

---

## 目录

1. [通用类型定义](#1-通用类型定义)
2. [通用接口](#2-通用接口)
3. [认证接口](#3-认证接口)
4. [用户管理接口](#4-用户管理接口)
5. [角色管理接口](#5-角色管理接口)
6. [部门管理接口](#6-部门管理接口)
7. [职称管理接口](#7-职称管理接口)
8. [设备管理接口](#8-设备管理接口)
9. [检测数据接口](#9-检测数据接口)
10. [审查任务接口](#10-审查任务接口)
11. [消息管理接口](#11-消息管理接口)
12. [审计日志接口](#12-审计日志接口)
13. [数据导出接口](#13-数据导出接口)
14. [系统管理接口](#14-系统管理接口)

---

## 1. 通用类型定义

### 1.1 通用响应结构

```typescript
interface ApiResponse<T = any> {
  code: number;        // 状态码，0=成功，非0=失败
  message: string;      // 响应消息
  data: T | null;       // 响应数据
}

interface PaginatedResponse<T> {
  total: number;       // 总记录数
  items: T[];          // 数据列表
}
```

### 1.2 通用分页参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | number | 否 | 跳过记录数，默认 0 |
| limit | number | 否 | 返回记录数，默认 100，最大 1000 |

### 1.3 认证说明

- **认证方式**: Bearer Token (JWT)
- **认证头**: `Authorization: Bearer <access_token>`
- **免认证接口**: 注册、登录、健康检查

### 1.4 用户相关类型

```typescript
interface User {
  user_id: string;              // UUID
  user_name: string;            // 用户名
  real_name: string;            // 真实姓名
  email: string | null;         // 邮箱
  phone: string | null;          // 电话
  employee_id: string | null;   // 工号
  department_id: number | null; // 部门ID
  title_id: number;             // 职称ID
  role_id: number;              // 角色ID
  avatar_url: string | null;     // 头像URL
  last_login: string | null;     // 最后登录时间
  created_at: string;            // 创建时间
}

interface UserRegisterRequest {
  user_name: string;            // 必填，3-50字符
  password: string;              // 必填，8-128字符
  real_name: string;             // 必填，1-50字符
  email?: string;               // 可选
  phone?: string;                // 可选，最多20字符
  employee_id?: string;         // 可选
  department_id?: number;       // 可选
  title_id?: number;            // 可选，默认9（注册员工）
}

interface UserLoginRequest {
  user_name: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;            // "bearer"
  expires_in: number;           // 过期时间（秒）
  user: User;
}

interface UserUpdateRequest {
  real_name?: string;
  email?: string;
  phone?: string;
  department_id?: number;
  title_id?: number;
  avatar_url?: string;
}

interface PasswordChangeRequest {
  old_password: string;
  new_password: string;          // 8-128字符
}

interface UserListResponse {
  total: number;
  users: User[];
}
```

### 1.5 部门相关类型

```typescript
interface Department {
  department_id: number;
  department_code: string;
  department_name: string;
  parent_id: number | null;
  created_at: string;
}

interface DepartmentCreateRequest {
  department_code: string;
  department_name: string;
  parent_id?: number;
}

interface DepartmentUpdateRequest {
  department_code?: string;
  department_name?: string;
  parent_id?: number;
}
```

### 1.6 职称相关类型

```typescript
interface Title {
  title_id: number;
  title_name: string;
}

interface TitleCreateRequest {
  title_name: string;
}

interface TitleUpdateRequest {
  title_name?: string;
}
```

### 1.7 角色相关类型

```typescript
interface Role {
  role_id: number;
  role_name: string;
  desc: string | null;
  is_system_role: boolean;
  permissions: any;
  created_at: string;
}

interface RoleCreateRequest {
  role_name: string;
  desc?: string;
  permissions?: any;
}

interface RoleUpdateRequest {
  role_name?: string;
  desc?: string;
  permissions?: any;
}
```

### 1.8 设备相关类型

```typescript
interface Device {
  device_id: string;              // UUID
  device_name: string;
  device_type: string;
  production_line_id: string;     // 生产线ID，UUID格式
  device_manager: string;          // 设备管理员ID
  ip_addr: string | null;
  mac_addr: string | null;
  status: string;                 // inactive | online | offline | removed
  device_upload_token: string | null;
  device_approval_id: string | null;
  installation_date: string | null;
  created_at: string | null;
}

interface DeviceCreateRequest {
  device_name: string;
  device_type: string;
  production_line_id: string;
  device_manager: string;
  ip_addr?: string;
  mac_addr?: string;
  installation_date?: string;
}

interface DeviceUpdateRequest {
  device_name?: string;
  device_type?: string;
  production_line_id?: string;
  device_manager?: string;
  ip_addr?: string;
  mac_addr?: string;
  status?: string;
}
```

### 1.9 生产线相关类型

```typescript
interface ProductionLine {
  production_line_id: string;      // UUID
  production_line_name: string;
  production_line_loc: string;
  production_line_manager: string | null;
  created_at: string | null;
}

interface ProductionLineCreateRequest {
  production_line_name: string;
  production_line_loc: string;
  production_line_manager?: string;
}

interface ProductionLineUpdateRequest {
  production_line_name?: string;
  production_line_loc?: string;
  production_line_manager?: string;
}
```

### 1.10 设备审批相关类型

```typescript
interface DeviceApproval {
  device_approval_id: string;
  device_name: string;
  device_type: string;
  production_line_id: string;
  device_manager: string;
  approval_send: string;
  approval_by: string | null;
  approval_status: string;         // pending | approved | rejected
  approval_comment: string | null;
  created_at: string | null;
}

interface DeviceApprovalRequest {
  approval_status: string;          // approved | rejected
  approval_comment?: string;
}
```

### 1.11 检测数据相关类型

```typescript
interface DetectionRecord {
  record_batch_id: string;          // UUID
  device_id: string;                 // UUID
  detect_count: number | null;
  pass_count: number | null;
  detect_info: any[];
  latest_upload_at: string | null;
  defect_details: DefectDetail[];
}

interface DefectDetail {
  defect_details_id: string;         // UUID
  record_batch_id: string;
  original_img: string;
  defect_count: number;
  details: any[];
  created_at: string | null;
}

interface DefectType {
  defect_type_id: number;
  defect_type_name: string;
  defect_category: string;
}
```

### 1.12 审查任务相关类型

```typescript
interface ReviewTask {
  review_task_id: string;            // UUID
  record_batch_id: string;
  defect_details_id: string;
  reviewer_id: string | null;
  review_status: string;             // pending | approved | rejected
  review_comment: string | null;
  created_at: string;
  reviewed_at: string | null;
}

interface ReviewTaskUpdateRequest {
  review_status: string;             // approved | rejected
  review_comment?: string;
}
```

### 1.13 消息相关类型

```typescript
interface SystemMessage {
  msg_id: string;                    // UUID
  receive_user: string;
  content: string;
  created_at: string;
  status: string;                     // read | unread
  readed_at: string | null;
}

interface SystemMessageCreateRequest {
  receive_user: string;
  content: string;
}

interface SystemMessageBatchCreateRequest {
  user_ids: string[];
  content: string;
}

interface Announcement {
  announcement_id: string;           // UUID
  receiver_type: string;              // all | department | role | title
  receive_target: number | null;
  content: string;
  created_at: string;
  send_user: string;
  expired: string;
}

interface AnnouncementCreateRequest {
  receiver_type?: string;             // 默认 all
  receive_target?: number;
  content: string;
  expired?: string;                   // 默认7天后
}

interface UserMessage {
  msg_id: string;                     // UUID
  send_user: string;
  receive_user: string;
  content: string;
  created_at: string;
  status: string;                     // read | unread
  readed_at: string | null;
  sender_name?: string;
  receiver_name?: string;
}

interface UserMessageCreateRequest {
  receive_user: string;
  content: string;
}
```

### 1.14 审计日志相关类型

```typescript
interface AuditLog {
  log_id: string;                     // UUID
  user_id: string;
  operation_type: string;
  operation_details: string | null;
  operation_result: string;           // success | failure
  error_msg: string | null;
  ip_addr: string | null;
  created_at: string;
}
```

---

## 2. 通用接口

### 2.1 健康检查

**接口**: `GET /common/health`

**说明**: 服务健康检查接口

**是否需要认证**: 否

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy"
  }
}
```

---

### 2.2 获取API列表

**接口**: `GET /admin/apis`

**说明**: 获取所有已注册的API列表

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取API列表成功",
  "data": {
    "apis": [...],
    "tags": [...]
  }
}
```

---

## 3. 认证接口

### 3.1 用户注册

**接口**: `POST /auth/register`

**说明**: 新用户注册（自动分配"注册员工"职称）

**是否需要认证**: 否

**请求体**: `UserRegisterRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "用户注册成功",
  "data": {...}
}
```

**错误码**:
- `400`: 用户名已存在

**备注**: 注册用户将自动分配"注册员工"职称（title_id=9），如需更改需管理员操作

---

### 3.2 用户登录

**接口**: `POST /auth/login`

**说明**: 用户登录获取Token

**是否需要认证**: 否

**请求体**: `UserLoginRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 14400,
    "user": {...}
  }
}
```

**错误码**:
- `401`: 用户名或密码错误

---

## 4. 用户管理接口

### 4.1 获取当前用户

**接口**: `GET /users/me`

**说明**: 获取当前登录用户信息

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取用户成功",
  "data": {...}
}
```

---

### 4.2 更新当前用户

**接口**: `PUT /users/me`

**说明**: 更新当前用户个人信息

**是否需要认证**: 是

**请求体**: `UserUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "用户信息更新成功",
  "data": {...}
}
```

---

### 4.3 修改密码

**接口**: `PUT /users/me/password`

**说明**: 修改当前用户密码

**是否需要认证**: 是

**请求体**: `PasswordChangeRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "密码修改成功",
  "data": null
}
```

**错误码**:
- `400`: 旧密码错误

---

### 4.4 批量创建用户

**接口**: `POST /users/batch`

**说明**: 批量创建用户。默认角色从角色缓存动态获取"无权限用户"，也可手动指定。

**是否需要认证**: 是

**请求体**:
```json
{
  "users": [
    {
      "user_name": "user1",
      "password": "password123",
      "real_name": "用户1",
      "email": "user1@example.com",
      "phone": "13800138001",
      "employee_id": "EMP001",
      "department_id": 1,
      "title_id": 9
    }
  ],
  "default_role_id": 1
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| users | array | 是 | 用户列表，每个用户包含 `user_name`、`password`、`real_name`，可选 `email`、`phone`、`employee_id`、`department_id`、`title_id` |
| default_role_id | number | 否 | 默认角色ID。不填时自动从角色缓存获取"无权限用户"，找不到则报错 |

**响应示例**:
```json
{
  "code": 0,
  "message": "批量创建完成：成功 3 人，失败 1 人",
  "data": {
    "success_count": 3,
    "failed_count": 1,
    "success_users": [...],
    "failed_users": [...]
  }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "无法获取默认角色ID：角色缓存中未找到\"无权限用户\"角色",
  "data": null
}
```

---

### 4.5 获取用户列表

**接口**: `GET /users`

**说明**: 分页获取用户列表

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | number | 否 | 跳过记录数，默认 0 |
| limit | number | 否 | 返回记录数，默认 100 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取用户列表成功",
  "data": {
    "total": 100,
    "users": [...]
  }
}
```

---

### 4.6 获取用户详情

**接口**: `GET /users/{user_id}`

**说明**: 根据用户ID获取详情

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户ID，UUID格式 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取用户成功",
  "data": {...}
}
```

**错误码**:
- `404`: 用户不存在

---

### 4.7 更新用户

**接口**: `PUT /users/{user_id}`

**说明**: 更新指定用户信息

**是否需要认证**: 是

**路径参数**: `user_id`

**请求体**: `UserUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "用户信息更新成功",
  "data": {...}
}
```

---

### 4.8 重置用户密码

**接口**: `PUT /users/{user_id}/password`

**说明**: 重置用户密码（管理员）

**是否需要认证**: 是

**路径参数**: `user_id`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| new_password | string | 是 | 新密码 |

**响应示例**:
```json
{
  "code": 0,
  "message": "密码重置成功",
  "data": null
}
```

---

### 4.9 删除用户（离职）

**接口**: `DELETE /users/{user_id}`

**说明**: 将用户角色改为无权限用户（离职），用户将无法登录系统

**是否需要认证**: 是

**路径参数**: `user_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "用户已离职（角色已更新为无权限用户）",
  "data": null
}
```

---

### 4.10 按部门查询用户

**接口**: `GET /users/by-department/{department_id}`

**说明**: 根据部门ID筛选用户列表

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| department_id | number | 部门ID |

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取部门用户成功",
  "data": {
    "total": 10,
    "users": [...]
  }
}
```

---

### 4.11 按职称查询用户

**接口**: `GET /users/by-title/{title_id}`

**说明**: 根据职称ID筛选用户列表

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| title_id | number | 职称ID |

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取职称用户成功",
  "data": {
    "total": 5,
    "users": [...]
  }
}
```

---

### 4.12 按角色查询用户

**接口**: `GET /users/by-role/{role_id}`

**说明**: 根据角色ID筛选用户列表

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| role_id | number | 角色ID |

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取角色用户成功",
  "data": {
    "total": 8,
    "users": [...]
  }
}
```

---

### 4.13 用户模糊搜索

**接口**: `GET /users/search`

**说明**: 按用户名/姓名/工号模糊搜索用户

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| skip | number | 否 | 跳过记录数 |
| limit | number | 否 | 返回记录数 |

**响应示例**:
```json
{
  "code": 0,
  "message": "搜索成功",
  "data": {
    "total": 3,
    "users": [...]
  }
}
```

---

## 5. 角色管理接口

### 5.1 获取角色列表

**接口**: `GET /roles`

**说明**: 获取所有角色列表

**是否需要认证**: 是

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取角色列表成功",
  "data": {
    "total": 5,
    "roles": [...]
  }
}
```

---

### 5.2 获取角色详情

**接口**: `GET /roles/{role_id}`

**说明**: 根据ID获取角色详情

**是否需要认证**: 是

**路径参数**: `role_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取角色成功",
  "data": {...}
}
```

---

### 5.3 创建角色

**接口**: `POST /roles`

**说明**: 创建新角色

**是否需要认证**: 是

**请求体**: `RoleCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "角色创建成功",
  "data": {...}
}
```

---

### 5.4 更新角色

**接口**: `PUT /roles/{role_id}`

**说明**: 更新角色信息

**是否需要认证**: 是

**路径参数**: `role_id`

**请求体**: `RoleUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "角色更新成功",
  "data": {...}
}
```

---

### 5.5 删除角色

**接口**: `DELETE /roles/{role_id}`

**说明**: 删除角色

**是否需要认证**: 是

**路径参数**: `role_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "角色删除成功",
  "data": null
}
```

---

## 6. 部门管理接口

### 6.1 获取部门列表

**接口**: `GET /departments`

**说明**: 获取所有部门列表

**是否需要认证**: 是

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取部门列表成功",
  "data": {
    "total": 10,
    "departments": [...]
  }
}
```

---

### 6.1.1 部门模糊搜索

**接口**: `GET /departments/search`

**说明**: 按部门名称或编号模糊搜索

**是否需要认证**: 是

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | string | 是 | 搜索关键词（至少1个字符） |
| skip | int | 否 | 跳过记录数（默认0） |
| limit | int | 否 | 返回记录数（默认100，最大1000） |

**响应示例**:
```json
{
  "code": 0,
  "message": "搜索成功",
  "data": {
    "total": 10,
    "departments": [...]
  }
}
```

---

### 6.2 获取部门详情

**接口**: `GET /departments/{department_id}`

**说明**: 根据ID获取部门详情

**是否需要认证**: 是

**路径参数**: `department_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取部门成功",
  "data": {...}
}
```

---

### 6.3 创建部门

**接口**: `POST /departments`

**说明**: 创建新部门

**是否需要认证**: 是

**请求体**: `DepartmentCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "部门创建成功",
  "data": {...}
}
```

---

### 6.4 更新部门

**接口**: `PUT /departments/{department_id}`

**说明**: 更新部门信息

**是否需要认证**: 是

**路径参数**: `department_id`

**请求体**: `DepartmentUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "部门更新成功",
  "data": {...}
}
```

---

### 6.5 删除部门

**接口**: `DELETE /departments/{department_id}`

**说明**: 删除部门（同时将关联用户的部门设为NULL）

**是否需要认证**: 是

**路径参数**: `department_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "部门删除成功",
  "data": null
}
```

**错误码**:
- `400`: 部门仍有下级部门
- `400`: 部门仍有用户使用

---

### 6.6 获取部门树形结构

**接口**: `GET /departments/list/tree`

**说明**: 返回部门层级关系树形结构

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取部门树形结构成功",
  "data": [
    {
      "department_id": 1,
      "department_code": "D001",
      "department_name": "总经办",
      "parent_id": null,
      "children": []
    },
    {
      "department_id": 2,
      "department_code": "D002",
      "department_name": "研发部",
      "parent_id": null,
      "children": [
        {
          "department_id": 3,
          "department_code": "D002-01",
          "department_name": "前端组",
          "parent_id": 2,
          "children": []
        }
      ]
    }
  ]
}
```

---

### 6.7 查询子部门

**接口**: `GET /departments/query/children/{department_id}`

**说明**: 根据父部门ID获取子部门列表

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| department_id | number | 父部门ID |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取子部门成功",
  "data": [
    {
      "department_id": 3,
      "department_code": "D002-01",
      "department_name": "前端组",
      "parent_id": 2
    }
  ]
}
```

---

## 7. 职称管理接口

### 7.1 获取职称列表

**接口**: `GET /titles`

**说明**: 获取所有职称列表

**是否需要认证**: 是

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取职称列表成功",
  "data": {
    "total": 10,
    "titles": [...]
  }
}
```

---

### 7.2 获取职称详情

**接口**: `GET /titles/{title_id}`

**说明**: 根据ID获取职称详情

**是否需要认证**: 是

**路径参数**: `title_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取职称成功",
  "data": {...}
}
```

---

### 7.3 创建职称

**接口**: `POST /titles`

**说明**: 创建新职称

**是否需要认证**: 是

**请求体**: `TitleCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "职称创建成功",
  "data": {...}
}
```

---

### 7.4 更新职称

**接口**: `PUT /titles/{title_id}`

**说明**: 更新职称信息

**是否需要认证**: 是

**路径参数**: `title_id`

**请求体**: `TitleUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "职称更新成功",
  "data": {...}
}
```

---

### 7.5 删除职称

**接口**: `DELETE /titles/{title_id}`

**说明**: 删除职称（同时将关联用户的外键设为默认值，不能删除默认职称）

**是否需要认证**: 是

**路径参数**: `title_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "职称删除成功",
  "data": null
}
```

**错误码**:
- `400`: 职称仍有用户使用

---

## 8. 设备管理接口

### 8.1 创建设备

**接口**: `POST /devices`

**说明**: 创建设备

**是否需要认证**: 是

**请求体**: `DeviceCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "设备创建成功",
  "data": {...}
}
```

---

### 8.2 获取设备列表

**接口**: `GET /devices`

**说明**: 分页获取设备列表。默认过滤掉状态为 `removed` 的设备。

**是否需要认证**: 是

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | number | 否 | 跳过记录数，默认 0 |
| limit | number | 否 | 返回记录数，默认 100，最大 1000 |
| status | string | 否 | 指定状态过滤。不填则返回非 `removed` 的设备；填 `removed` 则只返回已删除的设备 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备列表成功",
  "data": {
    "total": 10,
    "devices": [...]
  }
}
```

---

### 8.3 批量生成设备Token

**接口**: `POST /devices/tokens/batch-generate`

**说明**: 为多个设备批量生成上传Token

**是否需要认证**: 是

**请求体**:
```json
{
  "device_ids": ["uuid1", "uuid2"]
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "成功为 3 个设备生成Token",
  "data": {
    "count": 3,
    "devices": [...]
  }
}
```

---

### 8.4 导出设备Token列表

**接口**: `GET /devices/tokens/export`

**说明**: 导出所有设备的Token信息

**是否需要认证**: 是

**响应**: JSON文件下载

---

### 8.5 创建设备与生产线关联

**接口**: `POST /device-production-lines`

**说明**: 创建设备与生产线的关联

**是否需要认证**: 是

**请求体**:
```json
{
  "device_id": "uuid",
  "production_line_id": "uuid"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "创建设备生产线关联成功",
  "data": {...}
}
```

---

### 8.6 获取设备与生产线关联列表

**接口**: `GET /device-production-lines`

**说明**: 获取设备与生产线关联列表

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备生产线关联成功",
  "data": [...]
}
```

---

### 8.6.1 生产线模糊搜索

**接口**: `GET /device-production-lines/search`

**说明**: 按生产线名称或编号模糊搜索生产线

**是否需要认证**: 是

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | string | 是 | 搜索关键词（至少1个字符） |
| skip | int | 否 | 跳过记录数（默认0） |
| limit | int | 否 | 返回记录数（默认100，最大1000） |

**响应示例**:
```json
{
  "code": 0,
  "message": "搜索成功",
  "data": {
    "total": 10,
    "production_lines": [...]
  }
}
```

---

### 8.7 获取设备详情

**接口**: `GET /devices/{device_id}`

**说明**: 根据ID获取设备详情

**是否需要认证**: 是

**路径参数**: `device_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备成功",
  "data": {...}
}
```

---

### 8.8 更新设备

**接口**: `PUT /devices/{device_id}`

**说明**: 更新设备信息

**是否需要认证**: 是

**路径参数**: `device_id`

**请求体**: `DeviceUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "设备更新成功",
  "data": {...}
}
```

---

### 8.9 删除设备

**接口**: `DELETE /devices/{device_id}`

**说明**: 逻辑删除设备，将设备状态设置为 `removed`（非物理删除）。被删除的设备不会出现在列表查询结果中。

**是否需要认证**: 是

**路径参数**: `device_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "设备删除成功",
  "data": null
}
```

---

### 8.10 生成设备Token

**接口**: `POST /devices/{device_id}/token`

**说明**: 为设备生成上传Token

**是否需要认证**: 是

**路径参数**: `device_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "Token生成成功",
  "data": {
    "device_id": "uuid",
    "device_name": "设备名称",
    "device_upload_token": "token-value"
  }
}
```

---

### 8.11 获取设备Token

**接口**: `GET /devices/{device_id}/token`

**说明**: 获取设备的上传Token

**是否需要认证**: 是

**路径参数**: `device_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "device_id": "uuid",
    "device_name": "设备名称",
    "device_upload_token": "token-value"
  }
}
```

---

### 8.12 导出设备Token

**接口**: `GET /devices/{device_id}/token/export`

**说明**: 导出设备Token信息

**是否需要认证**: 是

**路径参数**: `device_id`

**响应**: JSON文件下载

---

### 8.13 获取生产线详情

**接口**: `GET /device-production-lines/{production_line_id}`

**说明**: 获取生产线详情

**是否需要认证**: 是

**路径参数**: `production_line_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {...}
}
```

---

### 8.14 更新生产线

**接口**: `PUT /device-production-lines/{production_line_id}`

**说明**: 更新生产线信息

**是否需要认证**: 是

**路径参数**: `production_line_id`

**请求体**: `ProductionLineUpdateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "更新成功",
  "data": {...}
}
```

---

### 8.15 删除生产线

**接口**: `DELETE /device-production-lines/{production_line_id}`

**说明**: 删除生产线

**是否需要认证**: 是

**路径参数**: `production_line_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

---

### 8.16 按生产线查询设备

**接口**: `GET /devices/query/by-production-line/{production_line_id}`

**说明**: 根据生产线ID筛选设备列表

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| production_line_id | string | 生产线ID，UUID格式 |

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取生产线设备成功",
  "data": {
    "total": 5,
    "devices": [...]
  }
}
```

---

### 8.17 按设备类型查询

**接口**: `GET /devices/query/by-type/{device_type}`

**说明**: 根据设备类型筛选设备列表

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| device_type | string | 设备类型 |

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备类型列表成功",
  "data": {
    "total": 10,
    "devices": [...]
  }
}
```

---

### 8.18 设备模糊搜索

**接口**: `GET /devices/list/search`

**说明**: 按设备名称模糊搜索设备

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| skip | number | 否 | 跳过记录数 |
| limit | number | 否 | 返回记录数 |

**响应示例**:
```json
{
  "code": 0,
  "message": "搜索成功",
  "data": {
    "total": 3,
    "devices": [...]
  }
}
```

---

### 8.19 设备在线状态统计

**接口**: `GET /devices/query/status-stats`

**说明**: 获取设备在线/离线数量统计

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备状态统计成功",
  "data": {
    "total": 100,
    "online": 85,
    "offline": 10,
    "inactive": 5,
    "removed": 0
  }
}
```

---

### 8.20 创建设备审批

**接口**: `POST /device-approvals`

**说明**: 创建设备审批记录

**是否需要认证**: 是

**请求体**:
```json
{
  "device_name": "设备名称",
  "device_type": "设备类型",
  "production_line_id": "uuid",
  "device_manager": "用户uuid"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "创建设备审批记录成功",
  "data": {...}
}
```

---

### 8.17 获取设备审批列表

**接口**: `GET /device-approvals`

**说明**: 获取设备审批列表

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备审批列表成功",
  "data": {
    "total": 10,
    "pending_approvals": [...]
  }
}
```

---

### 8.18 审批设备

**接口**: `PUT /device-approvals/{device_approval_id}`

**说明**: 审批设备

**是否需要认证**: 是

**路径参数**: `device_approval_id`

**请求体**: `DeviceApprovalRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "设备审批成功",
  "data": null
}
```

---

### 8.19 获取设备状态历史

**接口**: `GET /device-status-history/{device_id}`

**说明**: 获取设备状态变更历史

**是否需要认证**: 是

**路径参数**: `device_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备状态历史成功",
  "data": [...]
}
```

---

## 9. 检测数据接口

### 9.1 获取检测记录列表

**接口**: `GET /detection-records`

**说明**: 分页获取检测记录列表

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | number | 否 | 跳过记录数 |
| limit | number | 否 | 返回记录数 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取检测记录成功",
  "data": {
    "total": 100,
    "records": [...]
  }
}
```

---

### 9.2 获取检测记录详情

**接口**: `GET /detection-records/{record_batch_id}`

**说明**: 根据批次ID获取检测记录详情

**是否需要认证**: 是

**路径参数**: `record_batch_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取检测记录成功",
  "data": {...}
}
```

---

### 9.3 获取设备检测记录

**接口**: `GET /detection-records/query/by-device/{device_id}`

**说明**: 获取指定设备的检测记录

**是否需要认证**: 是

**路径参数**: `device_id`

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取检测记录成功",
  "data": {
    "total": 100,
    "records": [...]
  }
}
```

---

### 9.4 获取缺陷详情

**接口**: `GET /defect-details/{defect_details_id}`

**说明**: 获取缺陷详情

**是否需要认证**: 是

**路径参数**: `defect_details_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取缺陷详情成功",
  "data": {...}
}
```

---

### 9.5 获取缺陷类型列表

**接口**: `GET /defect-types`

**说明**: 获取所有缺陷类型

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取缺陷类型列表成功",
  "data": [...]
}
```

---

### 9.6 获取检测统计

**接口**: `GET /detection/stats`

**说明**: 获取检测统计数据

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取检测统计成功",
  "data": {...}
}
```

---

### 9.7 获取设备状态

**接口**: `GET /detection/device-status/{device_id}`

**说明**: 获取设备状态

**是否需要认证**: 是

**路径参数**: `device_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取设备状态成功",
  "data": {
    "device_id": "uuid",
    "status": "online",
    "last_heartbeat": "..."
  }
}
```

---

### 9.8 按时间范围查询检测记录

**接口**: `GET /detection-records/by-time`

**说明**: 根据时间段筛选检测记录

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 是 | 开始时间（ISO 8601格式） |
| end_time | string | 是 | 结束时间（ISO 8601格式） |
| skip | number | 否 | 跳过记录数 |
| limit | number | 否 | 返回记录数 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取检测记录成功",
  "data": {
    "total": 50,
    "records": [...]
  }
}
```

---

### 9.9 按缺陷类型查询记录

**接口**: `GET /detection-records/by-defect-type/{defect_type_id}`

**说明**: 根据缺陷类型筛选检测记录

**是否需要认证**: 是

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| defect_type_id | number | 缺陷类型ID |

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取缺陷类型记录成功",
  "data": {
    "total": 20,
    "records": [...]
  }
}
```

---

### 9.10 缺陷统计接口

**接口**: `GET /detection/defect-stats`

**说明**: 统计各类型缺陷数量

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取缺陷统计成功",
  "data": {
    "total_records": 1000,
    "total_defects": 150,
    "by_type": [
      {"defect_type_id": 1, "defect_type_name": "划痕", "count": 50},
      {"defect_type_id": 2, "defect_type_name": "凹陷", "count": 30}
    ]
  }
}
```

---

### 9.11 检测趋势接口

**接口**: `GET /detection/trend`

**说明**: 按时间分组统计检测数据

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 是 | 开始时间 |
| end_time | string | 是 | 结束时间 |
| group_by | string | 否 | 分组方式：day（默认）、week、month |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取检测趋势成功",
  "data": [
    {"date": "2024-01-01", "detect_count": 100, "pass_count": 90, "defect_count": 10},
    {"date": "2024-01-02", "detect_count": 120, "pass_count": 105, "defect_count": 15}
  ]
}
```

---

### 9.12 演示检测接口

**接口**: `POST /detection/demo`

**说明**: 演示检测接口

**是否需要认证**: 是

**请求体**:
```json
{
  "image_data": "base64编码的图片"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "检测完成",
  "data": {...}
}
```

---

### 9.13 缺陷趋势接口

**接口**: `GET /detection/defect-trend`

**说明**: 按天统计各类型缺陷数量

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 是 | 开始时间，ISO 8601格式 |
| end_time | string | 是 | 结束时间，ISO 8601格式 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取缺陷趋势成功",
  "data": [
    {
      "date": "2024-01-01",
      "defects": [
        {"defect_type_id": 1, "defect_type_name": "划痕", "count": 5},
        {"defect_type_id": 2, "defect_type_name": "凹陷", "count": 2},
        {"defect_type_id": 3, "defect_type_name": "裂纹", "count": 0}
      ]
    },
    {
      "date": "2024-01-02",
      "defects": [
        {"defect_type_id": 1, "defect_type_name": "划痕", "count": 3},
        {"defect_type_id": 2, "defect_type_name": "凹陷", "count": 1},
        {"defect_type_id": 3, "defect_type_name": "裂纹", "count": 4}
      ]
    }
  ]
}
```

---

## 10. 审查任务接口

### 10.1 获取审查任务列表

**接口**: `GET /review-tasks`

**说明**: 分页获取审查任务列表

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | number | 否 | 跳过记录数 |
| limit | number | 否 | 返回记录数 |
| status | string | 否 | 筛选状态 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取审查任务成功",
  "data": {
    "total": 100,
    "tasks": [...]
  }
}
```

---

### 10.2 获取审查任务详情

**接口**: `GET /review-tasks/{review_task_id}`

**说明**: 获取审查任务详情

**是否需要认证**: 是

**路径参数**: `review_task_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取审查任务成功",
  "data": {...}
}
```

---

### 10.3 更新审查任务

**接口**: `PUT /review-tasks/{review_task_id}`

**说明**: 更新审查任务状态、结果及详情，支持同步更新关联的检测记录缺陷数量

**是否需要认证**: 是

**路径参数**: 
| 参数 | 类型 | 说明 |
|------|------|------|
| review_task_id | string | 审查任务ID（UUID格式） |

**请求体**: `ReviewTaskUpdateRequest`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reviewer_id | UUID | 否 | 审查员ID |
| review_status | string | 否 | 审查状态：pending(待审查), completed(已完成), cancel(已取消), timeout(已超时) |
| review_result | string | 否 | 审查结果：confirmed(确认缺陷), false_positive(误报), uncertain(不确定), confusion(混淆) |
| review_defect_count | int | 否 | 审查确认的缺陷数量（非负整数）。当只传此参数时，缺陷数量更新为此值，detect_info置空 |
| has_details | bool | 否 | 是否有细节更改 |
| review_details | array | 否 | 审查后的缺陷详情，格式: [{'defect_type_id': ?, 'xyhw': (?,?,?,?), 'conf':?}, ...]。与review_defect_count同时存在时，优先使用review_defect_count的值 |
| review_comment | string | 否 | 审查备注 |

**缺陷数量更新规则**:
| 场景 | 行为 |
|------|------|
| 只传 `review_defect_count` | `detect_count=review_defect_count`，`detect_info=[]` |
| 只传 `review_details` | `detect_count=len(review_details)`，`detect_info`按类型统计 |
| 两者同时传 | `detect_count=review_defect_count`（优先使用参数值），`detect_info`按`review_details`统计 |

**状态转换规则**:
| 当前状态 | 允许转换到 |
|----------|------------|
| pending | pending, completed, cancel, timeout |
| completed | completed |
| cancel | cancel |
| timeout | pending, completed, cancel |

**响应示例**:
```json
{
  "code": 0,
  "message": "审查任务更新成功",
  "data": {
    "review_task_id": "uuid-string",
    "defect_details_id": "uuid-string",
    "assignee_id": "uuid-string",
    "reviewer_id": "uuid-string",
    "review_status": "completed",
    "review_result": "confirmed",
    "review_defect_count": 2,
    "has_details": true,
    "review_details": [{"defect_type_id": 1, "xyhw": [10, 20, 30, 40], "conf": 0.95}],
    "review_comment": "审查完成",
    "assignee_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T12:00:00Z"
  }
}
```

**错误响应**:
- 400: 参数验证失败（无效状态/结果、状态转换不允许、缺陷数量为负等）
- 404: 审查任务不存在
- 401: 未授权

---

### 10.4 获取我的审查任务

**接口**: `GET /review-tasks/me`

**说明**: 获取当前用户的审查任务

**是否需要认证**: 是

**查询参数**: skip, limit, status

**响应示例**:
```json
{
  "code": 0,
  "message": "获取我的审查任务成功",
  "data": {
    "total": 100,
    "tasks": [...]
  }
}
```

---

### 10.5 转交审查任务

**接口**: `POST /review-tasks/{review_task_id}/transfer`

**说明**: 转交审查任务给其他用户

**是否需要认证**: 是

**路径参数**: `review_task_id`

**请求体**:
```json
{
  "target_user_id": "用户uuid"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "转交成功",
  "data": null
}
```

---

## 11. 消息管理接口

### 11.1 建立SSE连接

**接口**: `GET /sse/connect`

**说明**: 建立服务端推送（SSE）连接，接收实时消息

**是否需要认证**: 是

**响应**: SSE流

---

### 11.2 发送SSE消息

**接口**: `POST /sse/send/{target_user_id}`

**说明**: 发送SSE消息给指定用户

**是否需要认证**: 是

**路径参数**: `target_user_id`

**请求体**:
```json
{
  "type": "string",
  "content": "string"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "消息发送成功",
  "data": null
}
```

---

### 11.3 创建系统消息

**接口**: `POST /system-messages`

**说明**: 创建系统消息

**是否需要认证**: 是

**请求体**: `SystemMessageCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "系统消息创建成功",
  "data": {...}
}
```

---

### 11.4 批量创建系统消息

**接口**: `POST /system-messages/batch`

**说明**: 批量创建系统消息

**是否需要认证**: 是

**请求体**: `SystemMessageBatchCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "批量创建系统消息成功",
  "data": {
    "count": 10
  }
}
```

---

### 11.5 获取我的系统消息

**接口**: `GET /system-messages/my`

**说明**: 获取当前用户的系统消息

**是否需要认证**: 是

**查询参数**: skip, limit, status

**响应示例**:
```json
{
  "code": 0,
  "message": "获取系统消息成功",
  "data": {
    "total": 100,
    "messages": [...]
  }
}
```

---

### 11.6 获取系统消息详情

**接口**: `GET /system-messages/{msg_id}`

**说明**: 获取系统消息详情

**是否需要认证**: 是

**路径参数**: `msg_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取系统消息成功",
  "data": {...}
}
```

---

### 11.7 标记系统消息已读

**接口**: `PUT /system-messages/{msg_id}/read`

**说明**: 标记单条系统消息为已读

**是否需要认证**: 是

**路径参数**: `msg_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "标记已读成功",
  "data": null
}
```

---

### 11.8 标记所有系统消息已读

**接口**: `PUT /system-messages/my/read-all`

**说明**: 标记所有系统消息为已读

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "全部标记已读成功",
  "data": null
}
```

---

### 11.9 创建公告

**接口**: `POST /announcements`

**说明**: 创建公告

**是否需要认证**: 是

**请求体**: `AnnouncementCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "公告创建成功",
  "data": {...}
}
```

---

### 11.10 获取公告列表

**接口**: `GET /announcements`

**说明**: 获取公告列表

**是否需要认证**: 是

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取公告列表成功",
  "data": {
    "total": 100,
    "announcements": [...]
  }
}
```

---

### 11.11 获取我的公告

**接口**: `GET /announcements/my`

**说明**: 获取当前用户可见的公告

**是否需要认证**: 是

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取公告成功",
  "data": {
    "total": 100,
    "announcements": [...]
  }
}
```

---

### 11.12 获取公告详情

**接口**: `GET /announcements/{announcement_id}`

**说明**: 获取公告详情

**是否需要认证**: 是

**路径参数**: `announcement_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取公告成功",
  "data": {...}
}
```

---

### 11.13 更新公告

**接口**: `PUT /announcements/{announcement_id}`

**说明**: 更新公告

**是否需要认证**: 是

**路径参数**: `announcement_id`

**请求体**:
```json
{
  "receiver_type": "all",
  "receive_target": null,
  "content": "新内容",
  "expired": "2024-12-31T23:59:59"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "公告更新成功",
  "data": {...}
}
```

---

### 11.14 删除公告

**接口**: `DELETE /announcements/{announcement_id}`

**说明**: 删除指定公告（同时删除关联的已读记录）

**是否需要认证**: 是

**路径参数**: `announcement_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "公告删除成功",
  "data": null
}
```

---

### 11.15 标记公告已读

**接口**: `PUT /announcements/{announcement_id}/read`

**说明**: 标记公告为已读

**是否需要认证**: 是

**路径参数**: `announcement_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "标记已读成功",
  "data": null
}
```

---

### 11.17 获取公告已读用户列表

**接口**: `GET /announcements/{announcement_id}/readers`

**说明**: 获取指定公告的已读用户列表

**是否需要认证**: 是

**路径参数**: `announcement_id`

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| skip | int | 否 | 跳过记录数（默认0） |
| limit | int | 否 | 返回记录数（默认100，最大1000） |

**响应示例**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "total": 10,
    "readers": [
      {
        "user_id": "uuid-string",
        "user_name": "用户名",
        "user_code": "用户编号",
        "readed_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

---

### 11.16 查询公告已读状态

**接口**: `GET /announcements/{announcement_id}/read-status`

**说明**: 查询当前用户是否已阅读指定公告

**是否需要认证**: 是

**路径参数**: `announcement_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "is_read": true
  }
}
```

---

### 11.17 创建用户消息

**接口**: `POST /user-messages`

**说明**: 创建用户消息

**是否需要认证**: 是

**请求体**: `UserMessageCreateRequest`

**响应示例**:
```json
{
  "code": 0,
  "message": "消息发送成功",
  "data": {...}
}
```

---

### 11.20 获取发送的消息

**接口**: `GET /user-messages/sent`

**说明**: 获取当前用户发送的消息

**是否需要认证**: 是

**查询参数**: skip, limit, status

**响应示例**:
```json
{
  "code": 0,
  "message": "获取发送消息成功",
  "data": {
    "total": 100,
    "messages": [...]
  }
}
```

---

### 11.21 获取收到的消息

**接口**: `GET /user-messages/received`

**说明**: 获取当前用户收到的消息

**是否需要认证**: 是

**查询参数**: skip, limit, status

**响应示例**:
```json
{
  "code": 0,
  "message": "获取收到消息成功",
  "data": {
    "total": 100,
    "messages": [...]
  }
}
```

---

### 11.18 获取消息详情

**接口**: `GET /user-messages/{msg_id}`

**说明**: 获取消息详情

**是否需要认证**: 是

**路径参数**: `msg_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取消息成功",
  "data": {...}
}
```

---

### 11.19 标记消息已读

**接口**: `PUT /user-messages/{msg_id}/read`

**说明**: 标记消息为已读

**是否需要认证**: 是

**路径参数**: `msg_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "标记已读成功",
  "data": null
}
```

---

### 11.20 标记所有收到消息已读

**接口**: `PUT /user-messages/received/read-all`

**说明**: 标记所有收到的消息为已读

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "全部标记已读成功",
  "data": null
}
```

---

## 12. 审计日志接口

### 12.1 获取审计日志列表

**接口**: `GET /audit-logs/logs`

**说明**: 分页获取审计日志

**是否需要认证**: 是

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | number | 否 | 跳过记录数 |
| limit | number | 否 | 返回记录数 |
| user_id | string | 否 | 筛选用户 |
| operation_type | string | 否 | 筛选操作类型 |
| operation_result | string | 否 | 筛选结果(success/failure) |
| start_date | string | 否 | 开始时间 |
| end_date | string | 否 | 结束时间 |

**响应示例**:
```json
{
  "code": 0,
  "message": "获取审计日志成功",
  "data": {
    "total": 1000,
    "logs": [...]
  }
}
```

---

### 12.2 获取审计日志详情

**接口**: `GET /audit-logs/logs/{log_id}`

**说明**: 获取审计日志详情

**是否需要认证**: 是

**路径参数**: `log_id`

**响应示例**:
```json
{
  "code": 0,
  "message": "获取审计日志成功",
  "data": {...}
}
```

---

### 12.3 获取用户审计日志

**接口**: `GET /audit-logs/users/{user_id}/logs`

**说明**: 获取指定用户的审计日志

**是否需要认证**: 是

**路径参数**: `user_id`

**查询参数**: skip, limit

**响应示例**:
```json
{
  "code": 0,
  "message": "获取审计日志成功",
  "data": {
    "total": 100,
    "logs": [...]
  }
}
```

---

## 13. 数据导出接口

### 13.1 获取可导出的表列表

**接口**: `GET /export/tables`

**说明**: 获取可导出的数据库表列表

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "获取导出表列表成功",
  "data": ["users", "devices", "departments", ...]
}
```

---

### 13.2 导出所有数据

**接口**: `GET /export/all`

**说明**: 导出所有数据为JSON文件

**是否需要认证**: 是

**响应**: JSON文件下载

---

### 13.3 导出指定表数据

**接口**: `GET /export/{table_name}`

**说明**: 导出指定表的数据

**是否需要认证**: 是

**路径参数**: `table_name`

**响应**: JSON文件下载

---

## 14. 系统管理接口

### 14.1 刷新角色缓存

**接口**: `POST /admin/role-cache/refresh`

**说明**: 手动刷新角色权限缓存

**是否需要认证**: 是

**响应示例**:
```json
{
  "code": 0,
  "message": "角色缓存刷新成功",
  "data": null
}
```

---

## 附录：错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |
| 504 | 请求超时 |

---

## 附录：认证头示例

```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```
