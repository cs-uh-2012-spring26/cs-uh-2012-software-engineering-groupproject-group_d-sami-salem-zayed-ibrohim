from http import HTTPStatus

from flask import current_app
from app.db.users import (
    CHANNEL_EMAIL,
    CHANNEL_TELEGRAM,
    CHANNELS,
    DEFAULT_NOTIFICATION_PREFERENCES,
    NOTIFICATION_PREFERENCES,
    ROLE_MEMBER,
    TELEGRAM_CHAT_ID,
    UserResource,
)


class UserNotificationService:
    def __init__(self):
        self.user_resource = UserResource()

    def get_notification_settings(self, user_id: str, role: str):
        error = self._validate_member(user_id, role)
        if error:
            return error

        user = self.user_resource.get_user_by_id(user_id)
        if not user:
            return {"message": "User not found"}, HTTPStatus.NOT_FOUND

        return self._settings_response(user), HTTPStatus.OK

    def update_notification_settings(self, user_id: str, role: str, data: dict):
        error = self._validate_member(user_id, role)
        if error:
            return error

        preferences, error = self._build_notification_preferences(data)
        if error:
            return error

        if not self.user_resource.update_notification_preferences(user_id, preferences):
            return {"message": "User not found"}, HTTPStatus.NOT_FOUND

        user = self.user_resource.get_user_by_id(user_id)
        return self._settings_response(user, "Notification preferences updated successfully"), HTTPStatus.OK

    def connect_telegram_from_webhook(self, data: dict):
        return self.connect_telegram_from_update((data or {}).get("message") or {})

    def connect_telegram_from_update(self, message: dict):
        text = message.get("text") or ""
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        link_token = self._extract_start_token(text)

        if not link_token or chat_id is None:
            return {"message": "Telegram /start token and chat id are required"}, HTTPStatus.BAD_REQUEST

        user = self.user_resource.connect_telegram(link_token, chat_id)
        if not user:
            return {"message": "Telegram link token not found"}, HTTPStatus.NOT_FOUND

        return {
            "message": "Telegram connected successfully",
            "telegram_connected": True,
        }, HTTPStatus.OK

    def _validate_member(self, user_id: str, role: str):
        if role != ROLE_MEMBER:
            return {"message": "Only members can configure notification preferences"}, HTTPStatus.FORBIDDEN

        if not user_id:
            return {"message": "Invalid authentication token"}, HTTPStatus.UNAUTHORIZED

        return None

    def _build_notification_preferences(self, data: dict):
        if not data:
            return None, ({"message": "Request body is required"}, HTTPStatus.BAD_REQUEST)

        channels = data.get(CHANNELS)
        if not isinstance(channels, list) or not channels:
            return None, ({"message": "channels must be a non-empty list"}, HTTPStatus.BAD_REQUEST)

        normalized_channels = []
        allowed_channels = {CHANNEL_EMAIL, CHANNEL_TELEGRAM}
        for channel in channels:
            if channel not in allowed_channels:
                return None, ({"message": f"Unsupported notification channel: {channel}"}, HTTPStatus.BAD_REQUEST)
            if channel not in normalized_channels:
                normalized_channels.append(channel)

        return {CHANNELS: normalized_channels}, None

    def _settings_response(self, user: dict, message: str = None):
        preferences = user.get(NOTIFICATION_PREFERENCES) or dict(DEFAULT_NOTIFICATION_PREFERENCES)
        response = {
            NOTIFICATION_PREFERENCES: preferences,
            "telegram_connected": bool(user.get(TELEGRAM_CHAT_ID)),
            "telegram_launch_url": self._build_launch_url(user),
        }
        if message:
            response["message"] = message
        return response

    def _build_launch_url(self, user: dict):
        bot_username = (current_app.config.get("TELEGRAM_BOT_USERNAME") or "sepr2bot").lstrip("@")
        user_id = str(user.get("_id"))
        link_token = self.user_resource.ensure_telegram_link_token(user_id)
        if not link_token:
            return None

        return f"https://t.me/{bot_username}?start={link_token}"

    def _extract_start_token(self, text: str):
        parts = text.split(maxsplit=1)
        if not parts or not parts[0].startswith("/start") or len(parts) < 2:
            return None
        return parts[1].strip()
