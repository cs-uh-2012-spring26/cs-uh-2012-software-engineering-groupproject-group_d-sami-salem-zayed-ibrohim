import json
import logging
import os
import threading
from urllib import request
from urllib.error import HTTPError, URLError

from app.services.user_notification_service import UserNotificationService


_polling_lock = threading.Lock()
_polling_thread = None


class TelegramBotPollingService:
    def __init__(self, app, bot_token: str = None, poll_timeout: int = None):
        self.app = app
        self.bot_token = bot_token or app.config.get("TELEGRAM_BOT_TOKEN")
        self.poll_timeout = poll_timeout or app.config.get("TELEGRAM_BOT_POLL_TIMEOUT", 20)
        self.offset = None
        self._stopped = threading.Event()

    def run_forever(self):
        if not self.bot_token:
            logging.warning("Telegram bot polling skipped because TELEGRAM_BOT_TOKEN is not configured")
            return

        webhook_deleted = False

        while not self._stopped.is_set():
            try:
                if not webhook_deleted:
                    self._delete_webhook()
                    webhook_deleted = True
                    logging.info("Telegram bot polling started")

                for update in self._get_updates():
                    self.offset = update.get("update_id", 0) + 1
                    self.process_update(update)
            except Exception as error:
                logging.exception("Telegram polling failed: %s", error)
                self._stopped.wait(5)

    def stop(self):
        self._stopped.set()

    def process_update(self, update: dict):
        message = (update or {}).get("message") or {}
        text = message.get("text") or ""
        chat = message.get("chat") or {}
        chat_id = chat.get("id")

        if not text.startswith("/start"):
            if chat_id:
                self._send_message(chat_id, "open the bot from the app's connect to telegram button.")
            return

        with self.app.app_context():
            response, status = UserNotificationService().connect_telegram_from_update(message)

        if not chat_id:
            return

        if 200 <= int(status) < 300:
            self._send_message(chat_id, "telegram connected. you can now receive class reminders here.")
        else:
            self._send_message(chat_id, response.get("message", "could not connect telegram."))

    def _get_updates(self):
        payload = {
            "timeout": self.poll_timeout,
            "allowed_updates": ["message"],
        }
        if self.offset is not None:
            payload["offset"] = self.offset

        result = self._telegram_api("getUpdates", payload, timeout=self.poll_timeout + 5)
        return result.get("result", [])

    def _delete_webhook(self):
        self._telegram_api("deleteWebhook", {"drop_pending_updates": False}, timeout=10)

    def _send_message(self, chat_id, text: str):
        self._telegram_api("sendMessage", {"chat_id": chat_id, "text": text}, timeout=10)

    def _telegram_api(self, method: str, payload: dict, timeout: int):
        telegram_request = request.Request(
            f"https://api.telegram.org/bot{self.bot_token}/{method}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(telegram_request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as error:
            raise Exception(f"Telegram {method} failed: {error}") from error

        if not result.get("ok"):
            raise ValueError(f"Telegram {method} failed: {result.get('description')}")

        return result


def start_telegram_bot_polling(app):
    if not app.config.get("TELEGRAM_BOT_POLLING_ENABLED"):
        return None

    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return None

    if app.config.get("TESTING"):
        return None

    global _polling_thread
    with _polling_lock:
        if _polling_thread and _polling_thread.is_alive():
            return _polling_thread

        service = TelegramBotPollingService(app)
        _polling_thread = threading.Thread(
            target=service.run_forever,
            name="telegram-bot-polling",
            daemon=True,
        )
        _polling_thread.start()
        return _polling_thread
