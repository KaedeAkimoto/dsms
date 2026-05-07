import pytest
import requests

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestDetectionAPI:
    """检测数据接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        self.test_device_id = "29b35bd7-7343-4ae8-8863-55ddaf55f7d8"
        sleep()

    def test_get_detection_records_success(self):
        """测试获取检测记录列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection-records",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_detection_records_with_pagination(self):
        """测试获取检测记录列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection-records?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_detection_records_unauthorized(self):
        """测试获取检测记录列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/detection-records")
        assert response.status_code == 401

    def test_get_defect_types_success(self):
        """测试获取缺陷类型列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/defect-types",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_defect_types_unauthorized(self):
        """测试获取缺陷类型列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/defect-types")
        assert response.status_code == 401

    def test_get_review_tasks_success(self):
        """测试获取审查任务列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/review-tasks",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_review_tasks_with_pagination(self):
        """测试获取审查任务列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/review-tasks?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_review_tasks_unauthorized(self):
        """测试获取审查任务列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/review-tasks")
        assert response.status_code == 401

    def test_get_review_tasks_me_success(self):
        """测试获取我的审查任务 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/review-tasks/me",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_detection_stats_success(self):
        """测试获取检测统计 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/stats?device_id={self.test_device_id}",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_detection_stats_unauthorized(self):
        """测试获取检测统计 - 公开接口无需认证"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/stats?device_id={self.test_device_id}"
        )
        assert response.status_code == 200

    def test_get_device_status_success(self):
        """测试获取设备状态 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/device-status/{self.test_device_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_get_device_status_not_found(self):
        """测试获取设备状态 - 设备不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/device-status/00000000-0000-0000-0000-000000000000",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_device_status_unauthorized(self):
        """测试获取设备状态 - 公开接口无需认证"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/device-status/{self.test_device_id}"
        )
        assert response.status_code == 200

    def test_get_defect_stats_success(self):
        """测试获取缺陷统计 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/defect-stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_get_defect_stats_with_time_range(self):
        """测试获取缺陷统计 - 带时间范围"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/defect-stats?start_time=2024-01-01T00:00:00Z&end_time=2026-12-31T23:59:59Z",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_get_defect_stats_unauthorized(self):
        """测试获取缺陷统计 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/detection/defect-stats")
        assert response.status_code == 401

    def test_get_defect_trend_success(self):
        """测试按天统计缺陷趋势 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/defect-trend?start_time=2024-01-01T00:00:00Z&end_time=2026-12-31T23:59:59Z",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_get_defect_trend_unauthorized(self):
        """测试按天统计缺陷趋势 - 未授权"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/detection/defect-trend?start_time=2024-01-01T00:00:00Z&end_time=2026-12-31T23:59:59Z"
        )
        assert response.status_code == 401

    def test_update_review_task_success(self):
        """测试更新审查任务 - 成功更新"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json={
                "review_status": "completed",
                "review_result": "confirmed",
                "review_defect_count": 2,
                "review_comment": "测试审查"
            }
        )
        assert response.status_code in [200, 404]

    def test_update_review_task_only_defect_count(self):
        """测试更新审查任务 - 只传缺陷数量"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json={
                "review_defect_count": 0
            }
        )
        assert response.status_code in [200, 404]

    def test_update_review_task_with_details(self):
        """测试更新审查任务 - 传缺陷详情"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json={
                "review_details": [
                    {"defect_type_id": 1, "xyhw": [10, 20, 30, 40], "conf": 0.95},
                    {"defect_type_id": 2, "xyhw": [50, 60, 70, 80], "conf": 0.88}
                ]
            }
        )
        assert response.status_code in [200, 404]

    def test_update_review_task_invalid_status(self):
        """测试更新审查任务 - 无效状态"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json={
                "review_status": "invalid_status",
                "review_result": "confirmed"
            }
        )
        assert response.status_code in [400, 404]

    def test_update_review_task_invalid_result(self):
        """测试更新审查任务 - 无效结果"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json={
                "review_status": "completed",
                "review_result": "invalid_result"
            }
        )
        assert response.status_code in [400, 404]

    def test_update_review_task_negative_defect_count(self):
        """测试更新审查任务 - 负数缺陷数量"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            headers=self.headers,
            json={
                "review_defect_count": -1
            }
        )
        assert response.status_code in [400, 404]

    def test_update_review_task_unauthorized(self):
        """测试更新审查任务 - 未授权"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/review-tasks/00000000-0000-0000-0000-000000000000",
            json={
                "review_status": "completed",
                "review_result": "confirmed"
            }
        )
        assert response.status_code == 401