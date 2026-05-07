# DSMS Server - 设备管理系统后端服务

## 项目简介

DSMS（Device Management System）是一个设备缺陷检测管理系统，提供完整的用户管理、设备管理、缺陷检测、权限控制等功能。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

修改 `config.toml` 文件配置数据库和安全设置。

### 3. 初始化数据

```bash
# 完整初始化（清空数据库并初始化所有数据）
python scripts/init_all.py all

# 或者分步执行
python scripts/init_all.py clear      # 清空数据库
python scripts/init_all.py init       # 初始化基础数据
python scripts/init_all.py init-roles # 初始化系统角色
python scripts/init_all.py init-admin # 创建超级管理员
```

### 4. 启动服务

```bash
python run.py
```

服务将自动检测可用端口并启动。

**端口自动检测**:
- 默认监听端口在 `config.toml` 中配置（默认 8001）
- 如果端口被占用，系统会自动查找下一个可用端口
- 查找范围：从配置端口开始，最多尝试 100 个端口

**请求超时配置**:
- 默认请求超时时间为 30 秒
- 可在 `config.toml` 的 `[server]` 部分调整 `request_timeout_seconds`
- 超时响应为 504 Gateway Timeout

**用户配置**:
- 默认职称ID在 `config.toml` 的 `[user]` 部分配置 `default_title_id`
- 默认值为 9（注册员工），新用户注册时自动分配此职称

## 修复脚本

当系统数据出现问题时，可以使用修复脚本：

```bash
# 重置超级管理员密码（默认 admin/admin123）
python scripts/repair.py reset-admin

# 重置系统职称数据
python scripts/repair.py reset-titles

# 重置系统角色
python scripts/repair.py reset-roles

# 执行所有修复操作
python scripts/repair.py all
```

## 文档索引

| 文档 | 位置 | 说明 |
|------|------|------|
| API文档 | [docs/API_DOCS.md](docs/API_DOCS.md) | 完整的 API 接口说明 |
| 角色权限 | [docs/ROLE_PERMISSIONS.md](docs/ROLE_PERMISSIONS.md) | 系统角色和权限说明 |
| 配置说明 | [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | config.toml 配置文件详解 |
| 模型需求 | [docs/MODEL_REQUIREMENTS.md](docs/MODEL_REQUIREMENTS.md) | 数据模型需求文档 |

## API访问

启动服务后访问：
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## 主要功能

### 核心模块

- 用户管理 - 用户注册、登录、信息维护（自动分配"注册员工"职称）
- 角色权限 - 基于角色的访问控制
- 设备管理 - 设备注册、状态管理
- 缺陷检测 - 图像检测、缺陷分类
- 审查任务 - 缺陷审核流程
- 消息通知 - 系统通知、用户消息

### 技术特性

- FastAPI 异步框架
- PostgreSQL 数据库
- JWT 认证
- WebSocket 实时通信
- YOLO 缺陷检测模型
- 自动端口检测

## 项目结构

```
dsms_server/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   │   └── v1/           # API v1 版本
│   ├── config/           # 配置文件
│   ├── core/             # 核心功能
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic 验证
│   ├── services/         # 业务逻辑
│   └── utils/            # 工具函数
├── docs/                 # 文档目录
├── scripts/              # 脚本工具
│   ├── init_all.py      # 初始化脚本（整合版）
│   └── repair.py        # 修复脚本
├── tests/                # 测试代码
├── detect_model/         # YOLO 模型
├── config.toml          # 配置文件
├── requirements.txt      # 依赖列表
└── run.py               # 启动脚本
```

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 添加文档字符串

## 许可证

MIT License