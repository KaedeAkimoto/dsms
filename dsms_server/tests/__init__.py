"""
DSMS API 测试脚本

使用超级管理员账号测试用户注册功能。

用法:
    python -m tests.test_register
"""

import sys
from pathlib import Path
import requests
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.server import server_config

settings = server_config.settings
BASE_URL = f"http://{settings.host}:{settings.port}"

SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "admin123"

TEST_USER_PREFIX = f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def login(username: str, password: str) -> tuple[str, dict]:
    """登录获取 token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"user_name": username, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        token = data["data"]["access_token"]
        user_info = data["data"]["user"]
        return token, user_info
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None, None


def get_roles(token: str) -> list:
    """获取角色列表"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/roles", headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["roles"]
    else:
        print(f"获取角色列表失败: {response.status_code} - {response.text}")
        return []


def assign_role(token: str, user_id: str, role_id: int) -> bool:
    """分配角色给用户"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/api/v1/users/{user_id}",
        headers=headers,
        json={"role_id": role_id}
    )
    if response.status_code == 200:
        return True
    else:
        print(f"分配角色失败: {response.status_code} - {response.text}")
        return False


def register_user(
    user_name: str,
    password: str = "Test123456",
    real_name: str = "测试用户",
    email: str = None,
    phone: str = None,
    employee_id: str = None
) -> tuple[bool, dict]:
    """注册新用户"""
    payload = {
        "user_name": user_name,
        "password": password,
        "real_name": real_name
    }
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if employee_id:
        payload["employee_id"] = employee_id

    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=payload)
    if response.status_code in [200, 201]:
        return True, response.json()
    else:
        return False, response.json()


def delete_user(token: str, user_id: str) -> bool:
    """删除用户"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/api/v1/users/{user_id}", headers=headers)
    return response.status_code == 200


def test_register():
    """测试用户注册功能"""
    print("\n" + "=" * 60)
    print("测试: 用户注册功能")
    print("=" * 60)

    print("\n[1] 超级管理员登录...")
    token, admin_info = login(SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD)
    if not token:
        print("超级管理员登录失败，测试终止")
        return False
    print(f"    登录成功: {admin_info['user_name']} (ID: {admin_info['user_id']})")

    print("\n[2] 获取角色列表...")
    roles = get_roles(token)
    if not roles:
        print("获取角色列表失败，测试终止")
        return False

    role_map = {r["role_name"]: r["role_id"] for r in roles}
    print(f"    角色列表:")
    for role in roles:
        print(f"      - {role['role_name']} (ID: {role['role_id']})")

    no_permission_role_id = role_map.get("无权限用户")
    hr_admin_role_id = role_map.get("人事管理员")
    device_admin_role_id = role_map.get("设备管理员")

    print("\n[3] 测试注册新用户（默认分配无权限角色）...")
    test_user_name = f"{TEST_USER_PREFIX}_auto"
    success, result = register_user(
        user_name=test_user_name,
        password="Test123456",
        real_name="自动分配角色测试用户"
    )

    if not success:
        print(f"    注册失败: {result}")
        return False

    new_user = result["data"]
    print(f"    注册成功!")
    print(f"    用户名: {new_user['user_name']}")
    print(f"    真实姓名: {new_user['real_name']}")
    print(f"    角色ID: {new_user['role_id']}")

    if new_user["role_id"] != no_permission_role_id:
        print(f"    警告: 角色ID不匹配! 期望: {no_permission_role_id}, 实际: {new_user['role_id']}")
    else:
        print(f"    验证通过: 用户被正确分配到无权限用户角色")

    print("\n[4] 测试注册时指定职称...")
    test_user_name2 = f"{TEST_USER_PREFIX}_with_title"
    success2, result2 = register_user(
        user_name=test_user_name2,
        password="Test123456",
        real_name="指定职称测试用户",
        email=f"{test_user_name2}@example.com",
        phone="13900000001"
    )

    if not success2:
        print(f"    注册失败: {result2}")
    else:
        new_user2 = result2["data"]
        print(f"    注册成功!")
        print(f"    用户名: {new_user2['user_name']}")
        print(f"    邮箱: {new_user2['email']}")
        print(f"    电话: {new_user2['phone']}")
        print(f"    角色ID: {new_user2['role_id']}")

    print("\n[5] 测试注册用户重复...")
    success3, result3 = register_user(
        user_name=test_user_name,
        password="Test123456",
        real_name="重复用户名"
    )

    if not success3:
        print(f"    正确拒绝重复用户名: {result3.get('detail', '用户名已存在')}")
    else:
        print(f"    错误: 不应该允许重复用户名注册!")

    print("\n[6] 测试为新注册用户分配角色...")
    if new_user["role_id"] == no_permission_role_id and hr_admin_role_id:
        print(f"    为用户 {new_user['user_name']} 分配人事管理员角色...")
        success_assign = assign_role(token, new_user["user_id"], hr_admin_role_id)
        if success_assign:
            print(f"    分配成功!")
        else:
            print(f"    分配失败")

    print("\n[7] 清理测试用户...")
    if new_user.get("user_id"):
        delete_user(token, new_user["user_id"])
        print(f"    已删除用户: {test_user_name}")
    if new_user2.get("user_id"):
        delete_user(token, new_user2["user_id"])
        print(f"    已删除用户: {test_user_name2}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_register()
