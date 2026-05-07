from app.db.bookings import (
    USER_EMAIL,
    USER_ID,
)
from app.db.users import (
    CHANNEL_EMAIL,
    CHANNELS,
    DEFAULT_NOTIFICATION_PREFERENCES,
    NOTIFICATION_PREFERENCES,
    TELEGRAM_CHAT_ID,
    UserResource,
)


class NotificationDispatcher:
    def __init__(self, strategies: dict, user_resource=None):
        self.strategies = strategies
        self.user_resource = user_resource or UserResource()

    def send_notification(self, booking: dict, subject: str, body: str):
        user = self.user_resource.get_user_by_id(booking.get(USER_ID)) or {}
        preferences = user.get(NOTIFICATION_PREFERENCES) or DEFAULT_NOTIFICATION_PREFERENCES
        channels = preferences.get(CHANNELS) or [CHANNEL_EMAIL]

        for channel in channels:
            strategy = self.strategies.get(channel)
            if not strategy:
                raise ValueError(f"Unsupported notification channel: {channel}")

            recipient = self._get_recipient(channel, booking, user)
            if not recipient:
                continue
            strategy.send_notification(recipient, subject, body)

    def _get_recipient(self, channel: str, booking: dict, user: dict):
        if channel == CHANNEL_EMAIL:
            return booking.get(USER_EMAIL)
        return user.get(TELEGRAM_CHAT_ID)
