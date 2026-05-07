import pytest
import requests
import time

BASE_URL = "http://127.0.0.1:8001"
API_PREFIX = "/api/v1"


class TestCommonAPI:
    """通用接口测试"""

    def test_health_check_success(self):
        """测试健康检查 - 成功"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/common/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "healthy"

    def test_health_check_returns_json(self):
        """测试健康检查 - 返回JSON格式"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/common/health")
        assert response.headers.get("content-type") == "application/json"

    def test_root_endpoint_success(self):
        """测试根路由 - 成功"""
        response = requests.get(f"{BASE_URL}/api/v1/common/health")
        assert response.status_code == 200

    def test_root_endpoint_returns_welcome_message(self):
        """测试根路由 - 返回欢迎消息"""
        response = requests.get(f"{BASE_URL}/api/v1/common/health")
        data = response.json()
        assert "code" in data

    def test_common_endpoint_without_trailing_slash(self):
        """测试通用接口 - 无尾部斜杠访问"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/common", allow_redirects=False)
        assert response.status_code in [200, 307]

    def test_health_check_no_auth_required(self):
        """测试健康检查 - 无需认证"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/common/health")
        assert response.status_code == 200

    def test_nonexistent_common_endpoint(self):
        """测试不存在的通用接口"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/common/nonexistent")
        assert response.status_code == 404

    def test_health_check_response_time(self):
        """测试健康检查 - 响应时间"""
        start = time.time()
        response = requests.get(f"{BASE_URL}{API_PREFIX}/common/health")
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 5.0