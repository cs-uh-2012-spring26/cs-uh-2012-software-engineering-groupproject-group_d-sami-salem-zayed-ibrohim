import json
from urllib import request
from urllib.error import HTTPError, URLError

from app.services.notification_service import NotificationService


class TelegramNotificationService(NotificationService):
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def send_notification(self, recipient: str, subject: str, body: str):
        if not self.bot_token:
            raise ValueError("Telegram bot token is not configured")
        if not recipient:
            raise ValueError("Telegram chat id is required")

        message = f"{subject}\n\n{body}"
        payload = json.dumps({
            "chat_id": recipient,
            "text": message,
        }).encode("utf-8")
        telegram_request = request.Request(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(telegram_request, timeout=10) as response:
                if response.status >= 400:
                    raise ValueError("Telegram notification failed")
        except (HTTPError, URLError) as error:
            raise Exception(f"Telegram notification failed: {error}") from error
