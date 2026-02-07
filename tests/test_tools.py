import os
import unittest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import urllib.parse

from tools import get_current_weather, wikipedia_summary, get_news_headlines, convert_currency, get_local_time

class TestTools(unittest.IsolatedAsyncioTestCase):

    @patch('tools.httpx.AsyncClient')
    @patch('tools.os.environ')
    async def test_get_current_weather_metric(self, mock_environ, mock_client_class):
        # Arrange
        api_key = "test_api_key"
        location = "London"
        format = "metric"
        expected_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

        mock_environ.get.return_value = api_key

        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15, "humidity": 70},
            "wind": {"speed": 5}
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_current_weather(mock_params, location, format=format)

        # Assert
        mock_client.get.assert_called_once_with(expected_url)
        expected_result = {
            "conditions": "clear sky",
            "temperature": "15°C",
            "humidity": "70%",
            "wind_speed": "5 m/s",
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.httpx.AsyncClient')
    @patch('tools.os.environ')
    async def test_get_current_weather_fahrenheit_default(self, mock_environ, mock_client_class):
        # Arrange
        api_key = "test_api_key"
        location = "New York"
        # Test default format
        expected_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial"

        mock_environ.get.return_value = api_key

        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "few clouds"}],
            "main": {"temp": 68, "humidity": 60},
            "wind": {"speed": 10}
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_current_weather(mock_params, location)

        # Assert
        mock_client.get.assert_called_once_with(expected_url)
        expected_result = {
            "conditions": "few clouds",
            "temperature": "68°F",
            "humidity": "60%",
            "wind_speed": "10 mph",
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.httpx.AsyncClient')
    async def test_wikipedia_summary_success(self, mock_client_class):
        # Arrange
        topic = "Python (programming language)"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Python (programming language)",
            "extract": "Python is a programming language...",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Python_(programming_language)"}}
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await wikipedia_summary(mock_params, topic)

        # Assert
        # urllib.parse.quote encodes ( and ) as %28 and %29
        mock_client.get.assert_called_once_with(f"https://en.wikipedia.org/api/rest_v1/page/summary/Python_%28programming_language%29")
        expected_result = {
            "title": "Python (programming language)",
            "summary": "Python is a programming language...",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.httpx.AsyncClient')
    async def test_wikipedia_summary_not_found(self, mock_client_class):
        # Arrange
        topic = "NonExistentTopic12345"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await wikipedia_summary(mock_params, topic)

        # Assert
        mock_params.result_callback.assert_awaited_once_with({"error": f"No Wikipedia article found for '{topic}'"})

    @patch('tools.httpx.AsyncClient')
    async def test_get_news_headlines_success(self, mock_client_class):
        # Arrange
        category = "Technology"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Technology": [
                {"title": "Tech News 1", "source": "Source 1"},
                {"title": "Tech News 2", "source": "Source 2"}
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_news_headlines(mock_params, category)

        # Assert
        mock_client.get.assert_called_once_with("https://ok.surf/api/v1/cors/news-feed")
        expected_result = {
            "category": "Technology",
            "headlines": [
                {"title": "Tech News 1", "source": "Source 1"},
                {"title": "Tech News 2", "source": "Source 2"}
            ]
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.httpx.AsyncClient')
    async def test_get_news_headlines_invalid_category(self, mock_client_class):
        # Arrange
        category = "InvalidCategory"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "World": []
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_news_headlines(mock_params, category)

        # Assert
        mock_params.result_callback.assert_awaited_once()
        args, _ = mock_params.result_callback.call_args
        self.assertIn("error", args[0])
        self.assertIn("Category 'InvalidCategory' not found", args[0]["error"])

    @patch('tools.httpx.AsyncClient')
    async def test_convert_currency_success(self, mock_client_class):
        # Arrange
        amount = 100
        from_currency = "USD"
        to_currency = "EUR"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "base_code": "USD",
            "rates": {"EUR": 0.85},
            "time_last_update_utc": "Fri, 06 Feb 2026 00:02:31 +0000"
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await convert_currency(mock_params, amount, from_currency, to_currency)

        # Assert
        mock_client.get.assert_called_once_with(f"https://open.er-api.com/v6/latest/USD")
        expected_result = {
            "from": "USD",
            "to": "EUR",
            "amount": 100,
            "converted_amount": 85.0,
            "rate": 0.85,
            "last_updated": "Fri, 06 Feb 2026 00:02:31 +0000"
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.httpx.AsyncClient')
    async def test_convert_currency_invalid_base(self, mock_client_class):
        # Arrange
        amount = 100
        from_currency = "INVALID"
        to_currency = "EUR"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "error",
            "error-type": "unsupported-code"
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await convert_currency(mock_params, amount, from_currency, to_currency)

        # Assert
        mock_params.result_callback.assert_awaited_once_with({"error": "Currency API error: unsupported-code"})

    @patch('tools.httpx.AsyncClient')
    async def test_convert_currency_invalid_target(self, mock_client_class):
        # Arrange
        amount = 100
        from_currency = "USD"
        to_currency = "INVALID"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "rates": {"EUR": 0.85}
        }
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await convert_currency(mock_params, amount, from_currency, to_currency)

        # Assert
        mock_params.result_callback.assert_awaited_once_with({"error": "Target currency 'INVALID' not found."})

    @patch('tools.httpx.AsyncClient')
    async def test_get_local_time_success(self, mock_client_class):
        # Arrange
        location = "Tokyo"
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Tokyo: 07:50:12+0900 Asia/Tokyo"
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_local_time(mock_params, location)

        # Assert
        mock_client.get.assert_called_once()
        args, _ = mock_client.get.call_args
        self.assertIn("Tokyo", args[0])
        self.assertIn("format=%l:+%T+%Z", args[0])

        expected_result = {
            "location": "Tokyo",
            "current_time": "07:50:12+0900",
            "timezone": "Asia/Tokyo"
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)

    @patch('tools.httpx.AsyncClient')
    async def test_get_local_time_no_location(self, mock_client_class):
        # Arrange
        mock_client = mock_client_class.return_value
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "London, United Kingdom: 22:50:12+0000 Europe/London"
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_params = Mock()
        mock_params.result_callback = AsyncMock()

        # Act
        await get_local_time(mock_params)

        # Assert
        mock_client.get.assert_called_once()
        expected_result = {
            "location": "London, United Kingdom",
            "current_time": "22:50:12+0000",
            "timezone": "Europe/London"
        }
        mock_params.result_callback.assert_awaited_once_with(expected_result)
