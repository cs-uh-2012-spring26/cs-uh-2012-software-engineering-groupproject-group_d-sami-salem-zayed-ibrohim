import pytest
from unittest.mock import patch
from urllib.error import HTTPError
from app.services.telegram_notification_service import TelegramNotificationService

# Unit test: Service should fail if token is empty
def test_telegram_service_input_validation():
    service = TelegramNotificationService(bot_token="")
    with pytest.raises(ValueError, match="bot token"):
        service.send_notification("123", "Title", "Body")

# Unit test: Ensure the service correctly handles Telegram API 500 errors
@patch("urllib.request.urlopen")
def test_telegram_network_failure(mock_urlopen):
    mock_urlopen.side_effect = HTTPError(None, 500, "Internal Server Error", None, None)
    service = TelegramNotificationService(bot_token="fake_token")
    
    with pytest.raises(Exception, match="Telegram notification failed"):
        service.send_notification("123", "Title", "Body")