import pytest
import requests

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestExportAPI:
    """数据导出接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_export_tables_success(self):
        """测试获取可导出表列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/tables",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "tables" in data["data"]

    def test_get_export_tables_unauthorized(self):
        """测试获取可导出表列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/export/tables")
        assert response.status_code == 401

    def test_export_all_data_json_success(self):
        """测试导出所有数据 - JSON格式"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/all?format=json",
            headers=self.headers
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"

    def test_export_all_data_excel_success(self):
        """测试导出所有数据 - Excel格式"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/all?format=excel",
            headers=self.headers
        )
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")

    def test_export_all_data_invalid_format(self):
        """测试导出所有数据 - 无效格式"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/all?format=invalid",
            headers=self.headers
        )
        assert response.status_code == 422

    def test_export_table_data_success(self):
        """测试导出指定表数据 - 成功导出"""
        tables_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/tables",
            headers=self.headers
        )
        if tables_response.status_code == 200:
            tables = tables_response.json()["data"]["tables"]
            if len(tables) > 0:
                table_name = tables[0]
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/export/{table_name}?format=json",
                    headers=self.headers
                )
                assert response.status_code == 200

    def test_export_table_data_not_found(self):
        """测试导出指定表数据 - 表不存在"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/nonexistent_table",
            headers=self.headers
        )
        assert response.status_code == 400

    def test_export_table_data_with_csv_format(self):
        """测试导出指定表数据 - CSV格式"""
        tables_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/tables",
            headers=self.headers
        )
        if tables_response.status_code == 200:
            tables = tables_response.json()["data"]["tables"]
            if len(tables) > 0:
                table_name = tables[0]
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/export/{table_name}?format=csv",
                    headers=self.headers
                )
                assert response.status_code == 200

    def test_export_table_data_with_excel_format(self):
        """测试导出指定表数据 - Excel格式"""
        tables_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/tables",
            headers=self.headers
        )
        if tables_response.status_code == 200:
            tables = tables_response.json()["data"]["tables"]
            if len(tables) > 0:
                table_name = tables[0]
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/export/{table_name}?format=excel",
                    headers=self.headers
                )
                assert response.status_code == 200

    def test_export_all_data_unauthorized(self):
        """测试导出所有数据 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/export/all")
        assert response.status_code == 401

    def test_export_table_data_unauthorized(self):
        """测试导出指定表数据 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/export/users")
        assert response.status_code == 401

    def test_get_export_tables_contains_users_table(self):
        """测试获取可导出表列表 - 包含users表"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export/tables",
            headers=self.headers
        )
        data = response.json()
        assert "users" in data["data"]["tables"]