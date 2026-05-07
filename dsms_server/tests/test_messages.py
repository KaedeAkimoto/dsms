import pytest
import requests
import uuid

from tests.test_utils import BASE_URL, API_PREFIX, get_headers, sleep


class TestMessagesAPI:
    """消息管理接口测试"""

    def setup_method(self):
        self.headers = get_headers()
        sleep()

    def test_get_system_messages_success(self):
        """测试获取系统消息列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/system-messages/my",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_system_messages_with_pagination(self):
        """测试获取系统消息列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/system-messages/my?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_system_messages_unauthorized(self):
        """测试获取系统消息列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/system-messages/my")
        assert response.status_code == 401

    def test_get_announcements_success(self):
        """测试获取公告列表 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_announcements_with_pagination(self):
        """测试获取公告列表 - 分页参数"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements?skip=0&limit=10",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_announcements_unauthorized(self):
        """测试获取公告列表 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/announcements")
        assert response.status_code == 401

    def test_get_user_messages_sent_success(self):
        """测试获取已发送消息 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/user-messages/sent",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_user_messages_received_success(self):
        """测试获取已接收消息 - 成功获取"""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/user-messages/received",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_get_user_messages_unauthorized(self):
        """测试获取用户消息 - 未授权"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/user-messages/sent")
        assert response.status_code == 401

    def test_create_system_message_success(self):
        """测试创建系统消息 - 成功创建"""
        users_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users",
            headers=self.headers
        )
        if users_response.status_code == 200:
            users = users_response.json()["data"]["users"]
            if len(users) > 1:
                target_user_id = users[1]["user_id"]
                payload = {
                    "receive_user": target_user_id,
                    "content": f"测试消息_{uuid.uuid4().hex[:8]}"
                }
                response = requests.post(
                    f"{BASE_URL}{API_PREFIX}/system-messages",
                    headers=self.headers,
                    json=payload
                )
                assert response.status_code in [200, 201]

    def test_create_system_message_missing_content(self):
        """测试创建系统消息 - 缺少内容"""
        payload = {"receive_user": "00000000-0000-0000-0000-000000000000"}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/system-messages",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 422

    def test_create_announcement_success(self):
        """测试创建公告 - 成功创建"""
        payload = {
            "title": f"测试公告_{uuid.uuid4().hex[:8]}",
            "content": "这是测试公告内容"
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/announcements",
            headers=self.headers,
            json=payload
        )
        assert response.status_code in [200, 201]

    def test_delete_announcement_success(self):
        """测试删除公告 - 成功删除"""
        payload = {
            "title": f"测试公告_{uuid.uuid4().hex[:8]}",
            "content": "这是测试公告内容"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/announcements",
            headers=self.headers,
            json=payload
        )
        assert create_response.status_code in [200, 201]
        announcement_id = create_response.json()["data"]["announcement_id"]

        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/announcements/{announcement_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "公告删除成功"

    def test_delete_announcement_not_found(self):
        """测试删除公告 - 公告不存在"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/announcements/{fake_id}",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_delete_announcement_unauthorized(self):
        """测试删除公告 - 未授权"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.delete(f"{BASE_URL}{API_PREFIX}/announcements/{fake_id}")
        assert response.status_code == 401

    def test_create_user_message_success(self):
        """测试创建用户消息 - 成功创建"""
        users_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users",
            headers=self.headers
        )
        if users_response.status_code == 200:
            users = users_response.json()["data"]["users"]
            if len(users) > 1:
                target_user_id = users[1]["user_id"]
                payload = {
                    "receive_user": target_user_id,
                    "content": f"用户消息_{uuid.uuid4().hex[:8]}"
                }
                response = requests.post(
                    f"{BASE_URL}{API_PREFIX}/user-messages",
                    headers=self.headers,
                    json=payload
                )
                assert response.status_code in [200, 201]

    def test_read_all_system_messages_success(self):
        """测试标记所有系统消息已读 - 成功"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/system-messages/my/read-all",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_read_all_user_messages_success(self):
        """测试标记所有用户消息已读 - 成功"""
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/user-messages/received/read-all",
            headers=self.headers
        )
        assert response.status_code == 200

    def test_get_announcement_readers_success(self):
        """测试获取公告已读用户列表 - 成功获取"""
        payload = {
            "title": f"测试公告_{uuid.uuid4().hex[:8]}",
            "content": "这是测试公告内容"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/announcements",
            headers=self.headers,
            json=payload
        )
        assert create_response.status_code in [200, 201]
        announcement_id = create_response.json()["data"]["announcement_id"]

        mark_read_response = requests.put(
            f"{BASE_URL}{API_PREFIX}/announcements/{announcement_id}/read",
            headers=self.headers
        )
        assert mark_read_response.status_code == 200

        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements/{announcement_id}/readers",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total" in data["data"]
        assert "readers" in data["data"]
        assert data["data"]["total"] >= 1

    def test_get_announcement_readers_not_found(self):
        """测试获取公告已读用户列表 - 公告不存在"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements/{fake_id}/readers",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_get_announcement_readers_unauthorized(self):
        """测试获取公告已读用户列表 - 未授权"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}{API_PREFIX}/announcements/{fake_id}/readers")
        assert response.status_code == 401

    def test_check_announcement_read_status_not_read(self):
        """测试查询公告已读状态 - 未读"""
        payload = {
            "title": f"测试公告_{uuid.uuid4().hex[:8]}",
            "content": "这是测试公告内容"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/announcements",
            headers=self.headers,
            json=payload
        )
        assert create_response.status_code in [200, 201]
        announcement_id = create_response.json()["data"]["announcement_id"]

        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements/{announcement_id}/read-status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["is_read"] == False

    def test_check_announcement_read_status_is_read(self):
        """测试查询公告已读状态 - 已读"""
        payload = {
            "title": f"测试公告_{uuid.uuid4().hex[:8]}",
            "content": "这是测试公告内容"
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/announcements",
            headers=self.headers,
            json=payload
        )
        assert create_response.status_code in [200, 201]
        announcement_id = create_response.json()["data"]["announcement_id"]

        mark_read_response = requests.put(
            f"{BASE_URL}{API_PREFIX}/announcements/{announcement_id}/read",
            headers=self.headers
        )
        assert mark_read_response.status_code == 200

        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements/{announcement_id}/read-status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["is_read"] == True

    def test_check_announcement_read_status_not_found(self):
        """测试查询公告已读状态 - 公告不存在"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/announcements/{fake_id}/read-status",
            headers=self.headers
        )
        assert response.status_code == 404

    def test_check_announcement_read_status_unauthorized(self):
        """测试查询公告已读状态 - 未授权"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}{API_PREFIX}/announcements/{fake_id}/read-status")
        assert response.status_code == 401