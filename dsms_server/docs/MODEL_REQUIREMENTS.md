

# 设备表
devices (
    device_id           vchar   PK, # uuid 
    device_name         vchar   NOT NULL, 
    device_type         vchar   NOT NULL, 
    device_upload_token vchar,
    production_lines_id vchar   FK  NOT NULL,
    device_manager      vchar   FK  NOT NULL,
    ip_addr,
    mac_addr,
    status              vchar DEFAULT 'inactive', # inactive | active | maintenance | fault | removed
    device_approval_id  vchar  FK,
    installation_date   date,
)


# 生产线表
production_lines (
    production_line_id         string  PK,         # uuid
    production_line_manager    string  FK,         # 允许空值
    production_line_loc        vchar   NOT NULL,
    production_line_name       vchar   NOT NULL
)


# 设备审批表
device_approvals (
    device_approval_id  string  PK, # uuid
    approval_send       string  FK  NOT NULL,
    approval_by         string  FK  NOT NULL,
    created_at          date    DEFAULT CURRENT_TIMESTAMP,
    processed_at        date,
    approval_status     vchar   DEFAULT 'pending', pending, approved, rejected 
)


# 设备历史状态表（时序数据）
device_status_history (
    history_id      string  PK,             # uuid
    device_id       string  FK  NOT NULL,
    status          string      NOT NULL,
    cpu_usage       float,
    memory_usage    float,
    network_latency int,
    created_at      timestamp DEFAULT CURRENT_TIMESTAMP,
)


# 缺陷类型表
defect_types (
    defect_type_id       int        PK,
    defect_type_name     vchar(50)          NOT NULL,
)


# 检测记录表，每个设备每time gap间隔内使用一条记录，时间间隔内第一次创建，后续都是更新
detection_records (
    record_batch_id     string  PK,             # 'BTH[year][mounth][day][hour][min // time gap + 1]'
    device_id           string  FK  NOT NULL, 
    detect_count        int,
    pass_count          int,
    detect_info         JSONB       NOT NULL    # [{'defect_type_id': ?, 'defect_count': ?}, ...], 无缺陷时为: []
    latest_upload_at    timestamp DEFAULT CURRENT_TIMESTAMP,
)


# 缺陷细节表，检测出缺陷后记录对应照片和缺陷详情
defect_details (
    defect_details_id   string      PK,             # uuid
    record_batch_id     string      FK  NOT NULL,
    original_img        vchar(500)      NOT NULL,   #imgurl
    defect_count        int,
    details             JSONB,                      # [{'defect_type_id': ?, 'xyhw': (?,?,?,?), 'conf':?}, ...]
)


# 人工审查表
review_tasks (
    review_task_id      vchar       PK,                 # uuid
    defect_details_id   vchar       FK  NOT NULL,
    assignee_id         vchar       FK  NOT NULL,       # 被分配任务的质检员
    reviewer_id         vchar       FK,                 # 实际审查的员工, 允许为空值
    review_status       vchar(20)   DEFAULT 'pending',  # pending, completed, cancel, timeout
    review_result       vchar(20),                      # confirmed, false_positive, uncertain, confusion
    review_defect_count int,
    has_details         bool,                           # 表示审查后是否有更改细节,未检查为NULL,无细节改变则false且review_details为NULL  
    review_details      JSONB,                          # 如果有值的格式：[{'defect_type_id': ?, 'xyhw': (?,?,?,?), 'conf':?}, ...]
    review_comment      TEXT,                           
    assignee_at         timestamp,
    completed_at        timestamp,
)


# 用户表
users (
    user_id         vchar       PK,         # uuid
    user_name       vchar(50)   NOT NULL,
    password_hash   vchar(255)  NOT NULL,   # bcrypt加盐hash
    employee_id     vchar(20)   UNIQUE,     # 工号
    real_name       vchar(50)   NOT NULL,
    email           vchar(100),
    phone           vchar(20),
    department_id   vchar       FK,         # 允许为空值
    title_id        FK          NOT NULL,              # 职称
    avatar_url      vchar(500),             # 头像url,允许为空值
    role_id         int         NOT NULL    FK,         # 角色id
    last_login      timestamp,
    created_at      timestamp   DEFAULT CURRENT_TIMESTAMP,  
)


# 角色表，角色决定用户权限
roles (
    role_id         SERIAL      PK,
    role_name       vchar(30)   UNIQUE NOT NULL
    desc            text,
    is_system_role  bool        DEFAULT false,
    permissions     JSONB,                                      # [{'api': ?, 'accessibility': ?}, ...], 允许为空值
    created_at      timestamp   DEFAULT CURRENT_TIMESTAMP,
)


# 部门表 
departments (
    department_id       int         PK,
    department_code     vchar(30)   UNIQUE  NOT NULL,           # 部门编码
    department_name     vchar(100)          NOT NULL,
    parent_id           int         FK,                         # 上级部门，顶级部门为NULL
    created_at          timestamp   DEFAULT CURRENT_TIMESTAMP,
)


# 职称表
titles (
    title_id            int         PK,
    title_name          vchar(30)   NOT NULL,
)


# 用户操作日志表
user_operation_logs (
    log_id              vchar       PK,                          # uuid
    user_id                         FK      NOT NULL,
    operation_type      vchar(50)           NOT NULL,
    operation_details   text,
    ip_addr,
    operation_result    vchar(20)   DEFAULT 'success',
    error_msg           text,
    created_at          timestamp   DEFAULT CURRENT_TIMESTAMP,
)


# 用户消息表
user_messages (
    msg_id              vchar       PK,
    send_user           FK          NOT NULL,
    receive_user        FK          NOT NULL,
    content             text        NOT NULL,
    created_at          timestamp   DEFAULT CURRENT_TIMESTAMP,
    status              vchar(20)   DEFAULT 'unread',           # read | unread    
    readed_at           timestamp,
)


# 系统消息表
system_messages (
    msg_id              vchar       PK,
    receive_user        vchar       Fk,     NOT NULL,
    content             text        NOT NULL,
    created_at          timestamp   DEFAULT CURRENT_TIMESTAMP,
    status              vchar(20)   DEFAULT 'unread',           # read | unread
    readed_at           timestamp,
)


# 公告表
announcements (
    announcement_id     vchar       PK,
    receiver_type       vchar       NOT NULL    DEFAULT 'all',  # all | department | role | title
    receive_target      int,        # 接受者的id,all为NULL, department时为department_id, role与 title同理。
    content             text        NOT NULL,
    created_at          timestamp   DEFAULT CURRENT_TIMESTAMP,
    send_user           vchar       FK          NOT NULL，
    expired             timestamp   NOT NULL, 
)


# 公告已读表
announcement_readers (
    announcement_id     FK  NOT NULL,
    user_id             FK  NOT NULL,
    readed_at           timestamp DEFAULT CURRENT_TIMESTAMP,
)
