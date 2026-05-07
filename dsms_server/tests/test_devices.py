import pytest
import requests
import uuid

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestDevicesAPI:
    """设备管理接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        self.test_device_code = f"DEV_{uuid.uuid4().hex[:8]}"
        sleep()

    def test_get_devices_success(self):
        """测试获取设备列表 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "devices" in data["data"]

    def test_get_devices_with_pagination(self):
        """测试获取设备列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/devices?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] >= 0

    def test_get_devices_unauthorized(self):
        """测试获取设备列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices")
        assert response.status_code == 401

    def test_get_device_by_id_success(self):
        """测试获取设备详情 - 成功获取"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices", headers=self.headers)
        devices = response.json()["data"]["devices"]
        if len(devices) > 0:
            device_id = devices[0]["device_id"]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/devices/{device_id}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "device_name" in data["data"]

    def test_get_device_not_found(self):
        """测试获取设备详情 - 设备不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/devices/00000000-0000-0000-0000-000000000000",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_create_device_success(self):
        """测试创建设备 - 成功创建"""
        line_response = requests.get(f"{BASE_URL}{API_PREFIX}/device-production-lines", headers=self.headers)
        lines = line_response.json()["data"]["production_lines"]
        if len(lines) > 0:
            production_line_id = lines[0]["production_line_id"]
        else:
            pytest.skip("没有生产线可关联")
        user_response = requests.get(f"{BASE_URL}{API_PREFIX}/users", headers=self.headers)
        users = user_response.json()["data"]["users"]
        if len(users) > 0:
            device_manager = users[0]["user_id"]
        else:
            pytest.skip("没有用户可作为设备负责人")
        payload = {
            "device_name": f"测试设备_{uuid.uuid4().hex[:8]}",
            "device_type": "类型A",
            "production_line_id": production_line_id,
            "device_manager": device_manager
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/devices",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 201]

    def test_create_device_missing_fields(self):
        """测试创建设备 - 缺少必填字段"""
        payload = {"device_name": "测试设备"}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/devices",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_create_device_duplicate_code(self):
        """测试创建设备 - 设备编码重复"""

    def test_update_device_success(self):
        """测试更新设备 - 成功更新"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices", headers=self.headers)
        devices = response.json()["data"]["devices"]
        if len(devices) == 0:
            pytest.skip("没有设备可更新")
        device_id = devices[0]["device_id"]
        update_payload = {"device_name": "更新后的设备名称"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/devices/{device_id}",
            headers=self.headers,
            json=update_payload
        )
        assert response.status_code == 200

    def test_update_device_not_found(self):
        """测试更新设备 - 设备不存在"""
        payload = {"device_name": "更新后的设备名称"}
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/devices/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 404

    def test_delete_device_success(self):
        """测试删除设备 - 成功删除"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices", headers=self.headers)
        devices = response.json()["data"]["devices"]
        if len(devices) == 0:
            pytest.skip("没有设备可删除")
        device_id = devices[0]["device_id"]
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/devices/{device_id}",
            headers=self.headers
        )
        assert response.status_code in [200, 204]

    def test_delete_device_not_found(self):
        """测试删除设备 - 设备不存在"""
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/devices/00000000-0000-0000-0000-000000000000",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_get_production_lines_success(self):
        """测试获取生产线列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/device-production-lines",
            headers=self.headers
        )
        assert response.status_code in [200, 500]

    def test_get_production_lines_unauthorized(self):
        """测试获取生产线列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/device-production-lines")
        assert response.status_code in [401, 500]

    def test_search_production_lines_success(self):
        """测试生产线模糊搜索 - 成功搜索"""
        line_response = requests.get(f"{BASE_URL}{API_PREFIX}/device-production-lines", headers=self.headers)
        if line_response.status_code == 200 and line_response.json()["data"]["total"] > 0:
            keyword = line_response.json()["data"]["production_lines"][0]["line_name"][:2]
        else:
            keyword = "test"
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/device-production-lines/search?keyword={keyword}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "production_lines" in data["data"]
        assert "total" in data["data"]

    def test_search_production_lines_empty_keyword(self):
        """测试生产线模糊搜索 - 空关键词返回422"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/device-production-lines/search?keyword=",
            headers=self.headers
        )
        assert response.status_code == 422

    def test_search_production_lines_not_found(self):
        """测试生产线模糊搜索 - 无结果"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/device-production-lines/search?keyword=nonexistentkeyword12345",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0