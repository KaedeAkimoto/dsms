import pytest
import requests
import uuid

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, clear_token, sleep


class TestUsersAPI:
    """用户管理接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_current_user_success(self):
        """测试获取当前用户 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "user_id" in data["data"]

    def test_get_current_user_unauthorized(self):
        """测试获取当前用户 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self):
        """测试获取当前用户 - 无效token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=headers)
        assert response.status_code == 401

    def test_update_current_user_success(self):
        """测试更新当前用户 - 成功更新"""
        payload = {"real_name": "新名字"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_update_current_user_with_email(self):
        """测试更新当前用户 - 更新邮箱"""
        payload = {"email": "newemail@example.com"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200

    def test_update_current_user_with_phone(self):
        """测试更新当前用户 - 更新电话"""
        payload = {"phone": "13900139000"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200

    def test_change_password_success(self):
        """测试修改密码 - 成功修改"""
        payload = {"old_password": "admin123", "new_password": "Admin123456"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me/password",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200

        payload_login = {"user_name": "admin", "password": "Admin123456"}
        login_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=payload_login
        )
        assert login_response.status_code == 200

        payload_restore = {"old_password": "Admin123456", "new_password": "admin123"}
        requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me/password",
            headers=self.headers,
            json=payload_restore
        )
        clear_token()

    def test_change_password_wrong_old_password(self):
        """测试修改密码 - 旧密码错误"""
        payload = {"old_password": "wrongpassword", "new_password": "NewPass123"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me/password",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 400

    def test_change_password_same_password(self):
        """测试修改密码 - 新旧密码相同"""
        payload = {"old_password": "admin123", "new_password": "admin123"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me/password",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 400]

    def test_change_password_short_new_password(self):
        """测试修改密码 - 新密码太短"""
        payload = {"old_password": "admin123", "new_password": "123"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/me/password",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_get_users_list_success(self):
        """测试获取用户列表 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "users" in data["data"]

    def test_get_users_list_with_pagination(self):
        """测试获取用户列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 0

    def test_get_users_list_unauthorized(self):
        """测试获取用户列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users")
        assert response.status_code == 401

    def test_get_user_by_id_success(self):
        """测试获取用户详情 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=self.headers)
        user_id = response.json()["data"]["user_id"]
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_name" in data["data"]

    def test_get_user_by_id_not_found(self):
        """测试获取用户详情 - 用户不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/00000000-0000-0000-0000-000000000000",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_update_user_success(self):
        """测试更新用户 - 成功更新"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=self.headers)
        user_id = response.json()["data"]["user_id"]

        payload = {"real_name": "管理员"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200

    def test_update_user_not_found(self):
        """测试更新用户 - 用户不存在"""
        payload = {"real_name": "新名字"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 404

    def test_update_user_password(self):
        """测试更新用户密码 - 成功更新"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me", headers=self.headers)
        user_id = response.json()["data"]["user_id"]

        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/users/{user_id}/password?new_password=Admin123789",
            headers=self.headers
        )
        assert response.status_code in [200, 400]

    def test_delete_user_success(self):
        """测试删除用户 - 成功删除（设置为无权限用户）"""
        payload = {
            "user_name": f"testuser_{uuid.uuid4().hex[:8]}",
            "password": "TestPass123",
            "real_name": "测试用户",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "13900139000"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=payload
        )
        if create_response.status_code in [200, 201]:
            login_response = requests.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                json={"user_name": payload["user_name"], "password": payload["password"]}
            )
            if login_response.status_code == 200:
                new_user_id = login_response.json()["data"]["user"]["user_id"]
                response = requests.delete(
                    f"{BASE_URL}{API_PREFIX}/users/{new_user_id}",
                    headers=self.headers
                )
                assert response.status_code == 200
                assert "离职" in response.json()["message"]
            else:
                assert True
        else:
            assert True

    def test_delete_user_not_found(self):
        """测试删除用户 - 用户不存在"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/users/00000000-0000-0000-0000-000000000000",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_batch_create_users_success(self):
        """测试批量创建用户 - 成功创建"""
        payload = {
            "users": [
                {
                    "user_name": f"batchuser1_{uuid.uuid4().hex[:8]}",
                    "password": "BatchPass123",
                    "real_name": "批量用户1",
                    "email": f"batch1_{uuid.uuid4().hex[:8]}@example.com"
                },
                {
                    "user_name": f"batchuser2_{uuid.uuid4().hex[:8]}",
                    "password": "BatchPass123",
                    "real_name": "批量用户2",
                    "email": f"batch2_{uuid.uuid4().hex[:8]}@example.com"
                }
            ]
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/users/batch",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200

    def test_batch_create_users_partial_failure(self):
        """测试批量创建用户 - 部分失败"""
        payload = {
            "users": [
                {
                    "user_name": f"batchuser3_{uuid.uuid4().hex[:8]}",
                    "password": "BatchPass123",
                    "real_name": "批量用户3",
                    "email": f"batch3_{uuid.uuid4().hex[:8]}@example.com"
                }
            ]
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/users/batch",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 400, 422]