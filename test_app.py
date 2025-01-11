import unittest
from unittest.mock import patch, MagicMock
import app
import os


class TestApp(unittest.TestCase):

    @patch("app.requests.get")
    def test_get_unread_entries(self, mock_get):
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entries": [
                {"id": 1, "title": "Test Entry", "content": "This is a test content."}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # 从环境变量获取配置
        miniflux_url = os.getenv("MINIFLUX_URL")
        miniflux_api_key = os.getenv("MINIFLUX_API_KEY")
        category_id = int(os.getenv("CATEGORY_ID", "4"))

        entries = app.get_unread_entries(miniflux_url, miniflux_api_key, category_id)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Test Entry")

    @patch("app.OpenAI")
    def test_generate_summary(self, MockOpenAI):
        # 模拟OpenAI API响应
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Summary"))]
        mock_client.chat.completions.create.return_value = mock_response

        summary = app.generate_summary(mock_client, "test-model", "Test content")
        self.assertEqual(summary, "Summary")

    @patch("app.OpenAI")
    def test_translate_content(self, MockOpenAI):
        # 模拟OpenAI API响应
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="翻译"))]
        mock_client.chat.completions.create.return_value = mock_response

        translation = app.translate_content(mock_client, "test-model", "Test content")
        self.assertEqual(translation, "翻译")

    @patch("app.requests.put")
    def test_update_entry_content(self, mock_put):
        # 模拟PUT请求响应
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        # 从环境变量获取配置
        miniflux_url = os.getenv("MINIFLUX_URL")
        miniflux_api_key = os.getenv("MINIFLUX_API_KEY")

        success = app.update_entry_content(
            miniflux_url,
            miniflux_api_key,
            1,
            "Original content",
            "Summary",
            "Translation",
        )
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
