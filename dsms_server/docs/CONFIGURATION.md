# DSMS 配置文件文档

> 本文档描述 DSMS 系统的配置文件 `config.toml` 中的所有配置项及其用法

## 配置文件位置

配置文件位于项目根目录：`config.toml`

---

## 配置项说明

### 1. 应用配置 (`[app]`)

应用的基本信息配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | string | `"DSMS"` | 应用名称 |
| `version` | string | `"1.0.0"` | 应用版本 |
| `debug` | boolean | `true` | 是否启用调试模式 |

**示例**:
```toml
[app]
name = "DSMS"
version = "1.0.0"
debug = true
```

---

### 2. 服务器配置 (`[server]`)

HTTP 服务器相关配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `host` | string | `"0.0.0.0"` | 服务器监听地址 |
| `port` | integer | `8001` | 服务器监听端口 |
| `request_timeout_seconds` | integer | `30` | 请求超时时间（秒） |

**示例**:
```toml
[server]
host = "0.0.0.0"
port = 8001
request_timeout_seconds = 30
```

**注意**:
- 如果 `port` 被占用，系统会自动查找下一个可用端口
- `request_timeout_seconds` 建议设置为 30-60 秒，根据业务需求调整

---

### 3. 数据库配置 (`[database]`)

PostgreSQL 数据库连接配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `url` | string | - | 数据库连接 URL |
| `pool_size` | integer | `10` | 数据库连接池大小 |
| `max_overflow` | integer | `20` | 连接池最大溢出数 |

**示例**:
```toml
[database]
url = "postgresql://dsms_user:dsms_password@localhost:5432/dsms_db"
pool_size = 10
max_overflow = 20
```

**URL 格式**:
```
postgresql://<用户名>:<密码>@<主机>:<端口>/<数据库名>
```

---

### 4. Redis 配置 (`[redis]`)

Redis 缓存和会话存储配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `url` | string | - | Redis 连接 URL |
| `max_connections` | integer | `10` | Redis 最大连接数 |

**示例**:
```toml
[redis]
url = "redis://:dsms_redis_password@localhost:6379/0"
max_connections = 10
```

**URL 格式**:
```
redis://:<密码>@<主机>:<端口>/<数据库号>
```

---

### 5. 安全配置 (`[security]`)

认证和安全相关配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `secret_key` | string | - | JWT 签名密钥（生产环境必须修改） |
| `algorithm` | string | `"HS256"` | JWT 签名算法 |
| `access_token_expire_minutes` | integer | `30` | 访问令牌过期时间（分钟） |

**示例**:
```toml
[security]
secret_key = "your-secret-key-here-change-in-production"
algorithm = "HS256"
access_token_expire_minutes = 30
```

**安全建议**:
- 生产环境必须使用强随机密钥
- 建议使用环境变量存储密钥
- 定期轮换密钥

---

### 6. CORS 配置 (`[cors]`)

跨域资源共享配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `origins` | string[] | - | 允许的来源地址列表 |
| `allow_credentials` | boolean | `true` | 是否允许携带凭证 |
| `allow_methods` | string[] | `["*"]` | 允许的 HTTP 方法 |
| `allow_headers` | string[] | `["*"]` | 允许的请求头 |

**示例**:
```toml
[cors]
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
allow_credentials = true
allow_methods = ["*"]
allow_headers = ["*"]
```

**生产环境建议**:
- 明确指定允许的 `origins`，不要使用通配符
- 限制 `allow_methods` 和 `allow_headers` 到实际需要的范围

---

### 7. 速率限制配置 (`[rate_limit]`)

API 速率限制配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_requests` | integer | `100` | 时间窗口内最大请求数 |
| `window_seconds` | integer | `60` | 时间窗口大小（秒） |

**示例**:
```toml
[rate_limit]
max_requests = 100
window_seconds = 60
```

---

### 8. 日志配置 (`[logging]`)

日志系统配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `level` | string | `"INFO"` | 日志级别 (DEBUG, INFO, WARNING, ERROR) |
| `format` | string | `"json"` | 日志格式 (json, text) |

**示例**:
```toml
[logging]
level = "INFO"
format = "json"
```

**日志级别说明**:
- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息

---

### 9. 文件上传配置 (`[upload]`)

文件上传相关配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_size` | integer | `10485760` | 最大文件大小（字节），默认 10MB |
| `allowed_image_types` | string[] | - | 允许的图片类型 |

**示例**:
```toml
[upload]
max_size = 10485760
allowed_image_types = ["image/jpeg", "image/png", "image/jpg"]
```

**常见文件大小**:
- 1MB = 1,048,576 字节
- 10MB = 10,485,760 字节
- 50MB = 52,428,800 字节

---

## 完整配置示例

```toml
[app]
name = "DSMS"
version = "1.0.0"
debug = true

[server]
host = "0.0.0.0"
port = 8001
request_timeout_seconds = 30

[database]
url = "postgresql://dsms_user:dsms_password@localhost:5432/dsms_db"
pool_size = 10
max_overflow = 20

[redis]
url = "redis://:dsms_redis_password@localhost:6379/0"
max_connections = 10

[security]
secret_key = "your-secret-key-here-change-in-production"
algorithm = "HS256"
access_token_expire_minutes = 30

[cors]
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
allow_credentials = true
allow_methods = ["*"]
allow_headers = ["*"]

[rate_limit]
max_requests = 100
window_seconds = 60

[logging]
level = "INFO"
format = "json"

[upload]
max_size = 10485760
allowed_image_types = ["image/jpeg", "image/png", "image/jpg"]
```

---

## 环境变量覆盖

配置项也可以通过环境变量覆盖，优先级为：

1. 环境变量
2. `config.toml` 配置
3. 默认值

**示例**:
```bash
# 覆盖数据库 URL
export DATABASE_URL="postgresql://user:pass@prod-host:5432/prod-db"

# 覆盖密钥
export SECRET_KEY="production-secret-key"

# 启动应用
python run.py
```

---

## 相关文档

- [API 接口文档](./API_DOCS.md)
- [角色与权限文档](./ROLE_PERMISSIONS.md)
- [README](../README.md)
