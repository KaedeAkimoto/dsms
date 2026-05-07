import pytest
import requests
import uuid

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestAuditLogsAPI:
    """审计日志接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.headers = get_headers()
        sleep()

    def test_get_audit_logs_success(self):
        """测试获取审计日志列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/logs",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "logs" in data["data"]

    def test_get_audit_logs_with_pagination(self):
        """测试获取审计日志列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/logs?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 0

    def test_get_audit_logs_unauthorized(self):
        """测试获取审计日志列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/audit-logs/logs")
        assert response.status_code == 401

    def test_get_audit_logs_with_user_filter(self):
        """测试获取审计日志列表 - 用户筛选"""
        users_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users",
            headers=self.headers
        )
        if users_response.status_code == 200:
            users = users_response.json()["data"]["users"]
            if len(users) > 0:
                user_id = users[0]["user_id"]
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/audit-logs/logs?user_id={user_id}",
                    headers=self.headers
                )
                assert response.status_code == 200

    def test_get_audit_logs_with_operation_type_filter(self):
        """测试获取审计日志列表 - 操作类型筛选"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/logs?operation_type=用户登录",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_audit_logs_with_result_filter(self):
        """测试获取审计日志列表 - 操作结果筛选"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/logs?operation_result=成功",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_audit_log_by_id_success(self):
        """测试获取审计日志详情 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/logs",
            headers=self.headers
        )
        logs = response.json()["data"]["logs"]
        if len(logs) > 0:
            log_id = logs[0]["log_id"]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/audit-logs/logs/{log_id}",
                headers=self.headers
            )
            assert response.status_code == 200

    def test_get_audit_log_by_id_not_found(self):
        """测试获取审计日志详情 - 日志不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/logs/00000000-0000-0000-0000-000000000000",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_get_user_audit_logs_success(self):
        """测试获取用户审计日志 - 成功获取"""
        users_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users",
            headers=self.headers
        )
        if users_response.status_code == 200:
            users = users_response.json()["data"]["users"]
            if len(users) > 0:
                user_id = users[0]["user_id"]
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/audit-logs/users/{user_id}/logs",
                    headers=self.headers
                )
                assert response.status_code == 200

    def test_get_user_audit_logs_not_found(self):
        """测试获取用户审计日志 - 用户不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/users/00000000-0000-0000-0000-000000000000/logs",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_user_audit_logs_with_pagination(self):
        """测试获取用户审计日志 - 分页参数"""
        users_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users",
            headers=self.headers
        )
        if users_response.status_code == 200:
            users = users_response.json()["data"]["users"]
            if len(users) > 0:
                user_id = users[0]["user_id"]
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/audit-logs/users/{user_id}/logs?skip=0&limit=10",
                    headers=self.headers
                )
                assert response.status_code == 200

    def test_get_user_audit_logs_unauthorized(self):
        """测试获取用户审计日志 - 未授权"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/audit-logs/users/00000000-0000-0000-0000-000000000000/logs"
        )
        assert response.status_code == 401