"""测试工具模块 - 共享登录逻辑"""
import requests
import time
import subprocess
import sys

BASE_URL = "http://127.0.0.1:8001"
API_PREFIX = "/api/v1"

session = requests.Session()
_shared_token = None
_shared_headers = None


def reset_admin_password():
    """重置admin密码为默认值"""
    try:
        result = subprocess.run(
            [sys.executable, "scripts/repair.py", "reset-admin"],
            cwd="/home/kaede/UserData/code_space/DSMS/dsms_server",
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception:
        return False


def get_token():
    """获取共享的访问令牌"""
    global _shared_token, _shared_headers
    if _shared_token is None:
        login_payload = {"user_name": "admin", "password": "admin123"}
        for attempt in range(3):
            response = session.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_payload)
            if response.status_code == 200:
                _shared_token = response.json()["data"]["access_token"]
                _shared_headers = {"Authorization": f"Bearer {_shared_token}"}
                return _shared_token
            elif response.status_code == 429:
                time.sleep(2)
            else:
                break
        if reset_admin_password():
            time.sleep(0.5)
            response = session.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_payload)
            if response.status_code == 200:
                _shared_token = response.json()["data"]["access_token"]
                _shared_headers = {"Authorization": f"Bearer {_shared_token}"}
                return _shared_token
        raise Exception(f"登录失败: {response.status_code} {response.text}")
    return _shared_token


def get_headers():
    """获取共享的请求头"""
    if _shared_headers is None:
        get_token()
    return _shared_headers


def clear_token():
    """清除共享的token，强制重新登录"""
    global _shared_token, _shared_headers
    _shared_token = None
    _shared_headers = None


def sleep(duration=0.5):
    """暂停指定时间，避免请求频率限制"""
    time.sleep(duration)