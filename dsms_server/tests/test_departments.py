import pytest
import requests
import uuid

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestDepartmentsAPI:
    """部门管理接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        self.test_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
        sleep()

    def test_get_departments_success(self):
        """测试获取部门列表 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/departments", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "departments" in data["data"]

    def test_get_departments_with_pagination(self):
        """测试获取部门列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/departments?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 0

    def test_get_departments_unauthorized(self):
        """测试获取部门列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/departments")
        assert response.status_code == 401

    def test_get_department_by_id_success(self):
        """测试获取部门详情 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/departments", headers=self.headers)
        departments = response.json()["data"]["departments"]
        if len(departments) > 0:
            dept_id = departments[0]["department_id"]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/departments/{dept_id}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "department_code" in data["data"]

    def test_get_department_not_found(self):
        """测试获取部门详情 - 部门不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/departments/99999",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_create_department_success(self):
        """测试创建部门 - 成功创建"""
        payload = {
            "department_code": self.test_dept_code,
            "department_name": f"测试部门_{uuid.uuid4().hex[:8]}"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 201]

    def test_create_department_with_parent(self):
        """测试创建部门 - 带上级部门"""
        parent_payload = {
            "department_code": f"PARENT_{uuid.uuid4().hex[:8]}",
            "department_name": "父部门"
        }
        parent_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=parent_payload
        )
        if parent_response.status_code in [200, 201]:
            parent_id = parent_response.json()["data"]["department_id"]
            child_payload = {
                "department_code": f"CHILD_{uuid.uuid4().hex[:8]}",
                "department_name": "子部门",
                "parent_id": parent_id
            }
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/departments",
                headers=self.headers,
                json=child_payload
            )
            assert response.status_code in [200, 201]

    def test_create_department_duplicate_code(self):
        """测试创建部门 - 部门编码已存在"""
        payload = {
            "department_code": self.test_dept_code,
            "department_name": "重复编码部门"
        }
        requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 400

    def test_create_department_missing_code(self):
        """测试创建部门 - 缺少部门编码"""
        payload = {"department_name": "测试部门"}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_create_department_missing_name(self):
        """测试创建部门 - 缺少部门名称"""
        payload = {"department_code": f"DEPT_{uuid.uuid4().hex[:8]}"}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_update_department_success(self):
        """测试更新部门 - 成功更新"""
        payload = {
            "department_code": f"UPDATE_{uuid.uuid4().hex[:8]}",
            "department_name": "测试部门"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            dept_id = create_response.json()["data"]["department_id"]
            update_payload = {"department_name": "更新后的部门名称"}
            response = requests.put(
                f"{BASE_URL}{API_PREFIX}/departments/{dept_id}",
                headers=self.headers,
                json=update_payload
            )
            assert response.status_code == 200

    def test_update_department_not_found(self):
        """测试更新部门 - 部门不存在"""
        payload = {"department_name": "更新后的部门名称"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/departments/99999",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 404

    def test_delete_department_success(self):
        """测试删除部门 - 成功删除"""
        payload = {
            "department_code": f"DEL_{uuid.uuid4().hex[:8]}",
            "department_name": "待删除部门"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            dept_id = create_response.json()["data"]["department_id"]
            response = requests.delete(
                f"{BASE_URL}{API_PREFIX}/departments/{dept_id}",
                headers=self.headers
            )
            assert response.status_code in [200, 204]

    def test_delete_department_not_found(self):
        """测试删除部门 - 部门不存在"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/departments/99999",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_delete_department_with_children(self):
        """测试删除部门 - 包含子部门"""
        parent_payload = {
            "department_code": f"PARENTDEL_{uuid.uuid4().hex[:8]}",
            "department_name": "待删除父部门"
        }
        parent_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/departments",
            headers=self.headers,
            json=parent_payload
        )
        if parent_response.status_code in [200, 201]:
            parent_id = parent_response.json()["data"]["department_id"]
            response = requests.delete(
                f"{BASE_URL}{API_PREFIX}/departments/{parent_id}",
                headers=self.headers
            )
            assert response.status_code in [200, 400, 404]

    def test_search_departments_success(self):
        """测试部门模糊搜索 - 成功搜索"""
        dept_response = requests.get(f"{BASE_URL}{API_PREFIX}/departments", headers=self.headers)
        if dept_response.status_code == 200 and dept_response.json()["data"]["total"] > 0:
            keyword = dept_response.json()["data"]["departments"][0]["department_name"][:2]
        else:
            keyword = "测试"
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/departments/search?keyword={keyword}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "departments" in data["data"]
        assert "total" in data["data"]

    def test_search_departments_empty_keyword(self):
        """测试部门模糊搜索 - 空关键词返回422"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/departments/search?keyword=",
            headers=self.headers
        )
        assert response.status_code == 422

    def test_search_departments_not_found(self):
        """测试部门模糊搜索 - 无结果"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/departments/search?keyword=nonexistentdept12345",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0