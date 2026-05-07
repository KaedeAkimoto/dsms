import pytest
import requests
import uuid

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestTitlesAPI:
    """职称管理接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        self.test_title_name = f"测试职称_{uuid.uuid4().hex[:8]}"
        sleep()

    def test_get_titles_success(self):
        """测试获取职称列表 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/titles", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "titles" in data["data"]

    def test_get_titles_with_pagination(self):
        """测试获取职称列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/titles?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 0

    def test_get_titles_unauthorized(self):
        """测试获取职称列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/titles")
        assert response.status_code == 401

    def test_get_title_by_id_success(self):
        """测试获取职称详情 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/titles", headers=self.headers)
        titles = response.json()["data"]["titles"]
        if len(titles) > 0:
            title_id = titles[0]["title_id"]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/titles/{title_id}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "title_name" in data["data"]

    def test_get_title_invalid_id(self):
        """测试获取职称详情 - 无效ID"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/titles/invalid",
            headers=self.headers
        )
        assert response.status_code == 422

    def test_create_title_success(self):
        """测试创建职称 - 成功创建"""
        payload = {
            "title_name": self.test_title_name,
            "title_level": "高级"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/titles",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 201]

    def test_create_title_duplicate_name(self):
        """测试创建职称 - 职称名重复"""
        payload = {
            "title_name": f"重复职称_{uuid.uuid4().hex[:8]}",
            "title_level": "中级"
        }
        requests.post(
            f"{BASE_URL}{API_PREFIX}/titles",
            headers=self.headers,
            json=payload
        )
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/titles",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [400, 409]

    def test_create_title_missing_name(self):
        """测试创建职称 - 缺少职称名称"""
        payload = {"title_level": "高级"}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/titles",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_update_title_success(self):
        """测试更新职称 - 成功更新"""
        payload = {
            "title_name": f"更新职称_{uuid.uuid4().hex[:8]}",
            "title_level": "中级"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/titles",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            title_id = create_response.json()["data"]["title_id"]
            update_payload = {"title_level": "高级"}
            response = requests.put(
                f"{BASE_URL}{API_PREFIX}/titles/{title_id}",
                headers=self.headers,
                json=update_payload
            )
            assert response.status_code == 200

    def test_update_title_not_found(self):
        """测试更新职称 - 职称不存在"""
        payload = {"title_level": "高级"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/titles/99999",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 404

    def test_delete_title_success(self):
        """测试删除职称 - 成功删除"""
        payload = {
            "title_name": f"删除职称_{uuid.uuid4().hex[:8]}",
            "title_level": "初级"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/titles",
            headers=self.headers,
            json=payload
        )
        if create_response.status_code in [200, 201]:
            title_id = create_response.json()["data"]["title_id"]
            response = requests.delete(
                f"{BASE_URL}{API_PREFIX}/titles/{title_id}",
                headers=self.headers
            )
            assert response.status_code in [200, 204]

    def test_delete_title_in_use(self):
        """测试删除职称 - 删除正在使用的职称（会自动迁移用户到默认职称）"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/titles/1",
            headers=self.headers
        )
        assert response.status_code in [200, 404, 400]

    def test_delete_title_not_found(self):
        """测试删除职称 - 职称不存在"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/titles/99999",
            headers=self.headers
        )
        assert response.status_code == 404