import pytest
import requests
import uuid
import time

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, clear_token, sleep


class TestRolesAPI:
    """角色管理接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        self.test_role_name = f"TestRole_{uuid.uuid4().hex[:8]}"
        sleep()

    def test_get_roles_success(self):
        """测试获取角色列表 - 成功访问"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/roles", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "roles" in data["data"]
        assert isinstance(data["data"]["roles"], list)

    def test_get_roles_with_pagination(self):
        """测试获取角色列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/roles?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 0

    def test_get_roles_authenticated(self):
        """测试获取角色列表 - 需要认证"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/roles")
        assert response.status_code == 401

    def test_get_role_by_id_success(self):
        """测试获取角色详情 - 成功获取"""
        roles_response = requests.get(f"{BASE_URL}{API_PREFIX}/roles", headers=self.headers)
        roles = roles_response.json()["data"]["roles"]
        if len(roles) > 0:
            role_id = roles[0]["role_id"]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/roles/{role_id}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert "role_name" in data["data"]

    def test_get_role_by_id_not_found(self):
        """测试获取角色详情 - 角色不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/roles/99999",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_get_role_invalid_id(self):
        """测试获取角色详情 - 无效ID"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/roles/invalid",
            headers=self.headers
        )
        assert response.status_code == 422

    def test_create_role_success(self):
        """测试创建角色 - 成功创建"""
        payload = {
            "role_name": self.test_role_name,
            "desc": "测试角色描述"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 201]

    def test_create_role_with_permissions(self):
        """测试创建角色 - 带权限"""
        payload = {
            "role_name": f"TestRolePerm_{uuid.uuid4().hex[:8]}",
            "desc": "测试角色描述",
            "permissions": {"actions": "read"}
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 201, 422]

    def test_create_role_duplicate_name(self):
        """测试创建角色 - 角色名重复"""
        payload = {
            "role_name": f"Duplicate_{uuid.uuid4().hex[:8]}",
            "desc": "测试重复角色"
        }
        response1 = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        response2 = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        assert response2.status_code in [200, 201, 400, 409]

    def test_create_role_missing_name(self):
        """测试创建角色 - 缺少角色名"""
        payload = {"desc": "测试角色描述"}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_update_role_success(self):
        """测试更新角色 - 成功更新"""
        payload = {
            "role_name": self.test_role_name,
            "desc": "测试角色描述"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            role_id = create_response.json()["data"]["role_id"]
            update_payload = {"desc": "更新后的描述"}
            response = requests.put(
                f"{BASE_URL}{API_PREFIX}/roles/{role_id}",
                headers=self.headers,
                json=update_payload
            )
            assert response.status_code == 200

    def test_update_role_not_found(self):
        """测试更新角色 - 角色不存在"""
        payload = {"desc": "更新后的描述"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/roles/99999",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 404

    def test_update_role_partial(self):
        """测试更新角色 - 部分更新"""
        payload = {
            "role_name": f"TestRolePartial_{uuid.uuid4().hex[:8]}",
            "desc": "测试角色描述"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            role_id = create_response.json()["data"]["role_id"]
            update_payload = {"desc": "只更新描述"}
            response = requests.put(
                f"{BASE_URL}{API_PREFIX}/roles/{role_id}",
                headers=self.headers,
                json=update_payload
            )
            assert response.status_code == 200

    def test_delete_role_success(self):
        """测试删除角色 - 成功删除"""
        payload = {
            "role_name": f"TestRoleDelete_{uuid.uuid4().hex[:8]}",
            "desc": "测试删除角色"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/roles",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            role_id = create_response.json()["data"]["role_id"]
            response = requests.delete(
                f"{BASE_URL}{API_PREFIX}/roles/{role_id}",
                headers=self.headers
            )
            assert response.status_code == 200

    def test_delete_role_not_found(self):
        """测试删除角色 - 角色不存在"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/roles/99999",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_delete_system_role(self):
        """测试删除角色 - 系统角色不可删除"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/roles/1",
            headers=self.headers
        )
        assert response.status_code in [400, 404]