import unittest
from unittest.mock import patch, Mock, AsyncMock
from tools import define_word
import httpx

class TestDictionaryTool(unittest.IsolatedAsyncioTestCase):

    @patch('httpx.AsyncClient.get')
    async def test_define_word_success(self, mock_get):
        # Arrange
        word = "hello"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "word": "hello",
                "phonetic": "/həˈləʊ/",
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "An utterance of \"hello\"; a greeting."},
                            {"definition": "A call for attention."}
                        ]
                    }
                ]
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await define_word(mock_params, word)

        # Assert
        mock_get.assert_called_once_with(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        expected_result = {
            "word": "hello",
            "phonetic": "/həˈləʊ/",
            "meanings": [
                {
                    "partOfSpeech": "noun",
                    "definitions": [
                        "An utterance of \"hello\"; a greeting.",
                        "A call for attention."
                    ]
                }
            ]
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('httpx.AsyncClient.get')
    async def test_define_word_not_found(self, mock_get):
        # Arrange
        word = "asdfghjkl"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await define_word(mock_params, word)

        # Assert
        mock_params.result_callback.assert_awaited_once_with({"error": f"Word '{word}' not found."})

    @patch('httpx.AsyncClient.get')
    async def test_define_word_api_error(self, mock_get):
        # Arrange
        word = "error"
        mock_get.side_effect = httpx.RequestError("API Down")

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await define_word(mock_params, word)

        # Assert
        mock_params.result_callback.assert_awaited_once()
        result = mock_params.result_callback.call_args[0][0]
        self.assertIn("error", result)
        self.assertIn("API request failed: API Down", result["error"])

if __name__ == '__main__':
    unittest.main()
