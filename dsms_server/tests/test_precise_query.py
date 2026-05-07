"""精准查询接口测试"""
import pytest
import requests
import uuid
from datetime import datetime, timedelta

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestUserPreciseQuery:
    """用户管理精准查询接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_users_by_department(self):
        """测试按部门查询用户"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]["total"] > 0:
            user = data["data"]["users"][0]
            if user.get("department_id"):
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/users/by-department/{user['department_id']}",
                    headers=self.headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "users" in data["data"]

    def test_get_users_by_department_not_found(self):
        """测试按不存在的部门查询用户"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/by-department/99999",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0

    def test_get_users_by_title(self):
        """测试按职称查询用户"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]["total"] > 0:
            user = data["data"]["users"][0]
            if user.get("title_id"):
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/users/by-title/{user['title_id']}",
                    headers=self.headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "users" in data["data"]

    def test_get_users_by_role(self):
        """测试按角色查询用户"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]["total"] > 0:
            user = data["data"]["users"][0]
            if user.get("role_id"):
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/users/by-role/{user['role_id']}",
                    headers=self.headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "users" in data["data"]

    def test_search_users(self):
        """测试用户模糊搜索"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/search?keyword=admin",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "users" in data["data"]

    def test_search_users_empty_keyword(self):
        """测试空关键词搜索 - 应返回422验证错误"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/search?keyword=",
            headers=self.headers
        )
        assert response.status_code == 422


class TestDevicePreciseQuery:
    """设备管理精准查询接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_devices_by_production_line(self):
        """测试按生产线查询设备"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]["total"] > 0:
            device = data["data"]["devices"][0]
            if device.get("production_line_id"):
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/devices/query/by-production-line/{device['production_line_id']}",
                    headers=self.headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "devices" in data["data"]

    def test_get_devices_by_type(self):
        """测试按设备类型查询"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/devices", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]["total"] > 0:
            device = data["data"]["devices"][0]
            if device.get("device_type"):
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/devices/query/by-type/{device['device_type']}",
                    headers=self.headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "devices" in data["data"]

    def test_search_devices(self):
        """测试设备模糊搜索"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/devices/list/search?keyword=device",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "devices" in data["data"]

    def test_get_device_status_stats(self):
        """测试设备状态统计"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/devices/query/status-stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total" in data["data"]
        assert "online" in data["data"]
        assert "offline" in data["data"]
        assert "inactive" in data["data"]


class TestDetectionPreciseQuery:
    """检测数据精准查询接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_detection_records_by_time(self):
        """测试按时间范围查询检测记录"""
        end_time = datetime.utcnow().isoformat() + "Z"
        start_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection-records/by-time?start_time={start_time}&end_time={end_time}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total" in data["data"]
        assert "records" in data["data"]

    def test_get_detection_records_by_defect_type(self):
        """测试按缺陷类型查询检测记录"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/defect-types", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]:
            defect_type = data["data"][0]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/detection-records/by-defect-type/{defect_type['defect_type_id']}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200

    def test_get_defect_stats(self):
        """测试缺陷统计"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/defect-stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_defect_stats_with_time_range(self):
        """测试带时间范围的缺陷统计"""
        end_time = datetime.utcnow().isoformat() + "Z"
        start_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/defect-stats?start_time={start_time}&end_time={end_time}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_detection_trend(self):
        """测试检测趋势"""
        end_time = datetime.utcnow().isoformat() + "Z"
        start_time = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/trend?start_time={start_time}&end_time={end_time}&group_by=day",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestDepartmentTree:
    """部门树形结构接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_department_tree(self):
        """测试获取部门树形结构"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/departments/list/tree",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_department_children(self):
        """测试获取子部门列表"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/departments", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["data"]["total"] > 0:
            department = data["data"]["departments"][0]
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/departments/query/children/{department['department_id']}",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200