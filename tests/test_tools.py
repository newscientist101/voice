import os
import unittest
from unittest.mock import patch, Mock, AsyncMock

from tools import get_current_weather, define_word

class TestTools(unittest.IsolatedAsyncioTestCase):

    @patch('tools.requests.get')
    @patch('tools.os.environ')
    async def test_get_current_weather_metric(self, mock_environ, mock_get):
        # Arrange
        api_key = "test_api_key"
        location = "London"
        format = "metric"
        expected_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={format}"

        mock_environ.get.return_value = api_key

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15, "humidity": 70},
            "wind": {"speed": 5}
        }
        mock_get.return_value = mock_response

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_current_weather(mock_params, location, format=format)

        # Assert
        mock_get.assert_called_once_with(expected_url)
        expected_result = {
            "conditions": "clear sky",
            "temperature": "15°C",
            "humidity": "70%",
            "wind_speed": "5 m/s",
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.requests.get')
    @patch('tools.os.environ')
    async def test_get_current_weather_fahrenheit_default(self, mock_environ, mock_get):
        # Arrange
        api_key = "test_api_key"
        location = "New York"
        # Test default format
        expected_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial"

        mock_environ.get.return_value = api_key

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "few clouds"}],
            "main": {"temp": 68, "humidity": 60},
            "wind": {"speed": 10}
        }
        mock_get.return_value = mock_response

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_current_weather(mock_params, location)

        # Assert
        mock_get.assert_called_once_with(expected_url)
        expected_result = {
            "conditions": "few clouds",
            "temperature": "68°F",
            "humidity": "60%",
            "wind_speed": "10 mph",
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.requests.get')
    async def test_define_word_success(self, mock_get):
        # Arrange
        word = "hello"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "word": "hello",
                "phonetic": "həˈləʊ",
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "A greeting."}
                        ]
                    }
                ]
            }
        ]
        mock_get.return_value = mock_response

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await define_word(mock_params, word)

        # Assert
        expected_result = {
            "word": "hello",
            "phonetic": "həˈləʊ",
            "meanings": [
                {
                    "part_of_speech": "noun",
                    "definitions": ["A greeting."]
                }
            ]
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.requests.get')
    async def test_define_word_not_found(self, mock_get):
        # Arrange
        word = "nonexistentword"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await define_word(mock_params, word)

        # Assert
        expected_result = {"error": f"Word '{word}' not found."}
        mock_params.result_callback.assert_awaited_once_with(expected_result)