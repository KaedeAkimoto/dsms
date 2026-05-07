import pytest
import requests
import uuid

BASE_URL = "http://127.0.0.1:8001"
API_PREFIX = "/api/v1"


class TestAuthAPI:
    """认证接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_username = f"testuser_{uuid.uuid4().hex[:8]}"
        self.test_password = "Test123456"
        self.test_real_name = "测试用户"

    def test_register_success(self):
        """测试用户注册 - 成功注册"""
        payload = {
            "user_name": self.test_username,
            "password": self.test_password,
            "real_name": self.test_real_name,
            "email": f"{self.test_username}@example.com"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["code"] in [200, 201]

    def test_register_with_email(self):
        """测试用户注册 - 带邮箱"""
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        payload = {
            "user_name": username,
            "password": "Test123456",
            "real_name": "测试用户",
            "email": f"{username}@example.com"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code in [200, 201]

    def test_register_with_phone(self):
        """测试用户注册 - 带手机号"""
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        payload = {
            "user_name": username,
            "password": "Test123456",
            "real_name": "测试用户",
            "phone": "13900139000"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code in [200, 201]

    def test_register_duplicate_username(self):
        """测试用户注册 - 用户名已存在"""
        payload = {
            "user_name": "admin",
            "password": "Test123456",
            "real_name": "测试用户"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code == 400

    def test_register_missing_required_fields(self):
        """测试用户注册 - 缺少必填字段"""
        payload = {"user_name": "testuser"}
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_short_password(self):
        """测试用户注册 - 密码太短"""
        payload = {
            "user_name": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "123",
            "real_name": "测试用户"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code == 422

    def test_login_success(self):
        """测试用户登录 - 成功登录"""
        payload = {"user_name": "admin", "password": "admin123"}
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]

    def test_login_with_valid_token(self):
        """测试用户登录 - 带有效token验证"""
        payload = {"user_name": "admin", "password": "admin123"}
        login_response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
        token = login_response.json()["data"]["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        verify_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers=headers
        )
        assert verify_response.status_code == 200

    def test_login_invalid_username(self):
        """测试用户登录 - 用户名错误"""
        payload = {"user_name": "nonexistent", "password": "Test123456"}
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
        assert response.status_code == 401

    def test_login_invalid_password(self):
        """测试用户登录 - 密码错误"""
        payload = {"user_name": "admin", "password": "wrongpassword"}
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
        assert response.status_code == 401

    def test_login_missing_username(self):
        """测试用户登录 - 缺少用户名"""
        payload = {"password": "Test123456"}
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
        assert response.status_code == 422

    def test_login_missing_password(self):
        """测试用户登录 - 缺少密码"""
        payload = {"user_name": "admin"}
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=payload)
        assert response.status_code == 422

    def test_login_empty_payload(self):
        """测试用户登录 - 空载荷"""
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json={})
        assert response.status_code == 422

    def test_register_empty_username(self):
        """测试用户注册 - 用户名为空"""
        payload = {
            "user_name": "",
            "password": "Test123456",
            "real_name": "测试用户"
        }
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=payload)
        assert response.status_code == 422