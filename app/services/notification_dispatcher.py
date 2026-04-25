from app.db.bookings import (
    CHANNEL_EMAIL,
    CHANNELS,
    DEFAULT_NOTIFICATION_PREFERENCES,
    NOTIFICATION_PREFERENCES,
    TELEGRAM_CHAT_ID,
    USER_EMAIL,
)


class NotificationDispatcher:
    def __init__(self, strategies: dict):
        self.strategies = strategies

    def send_notification(self, booking: dict, subject: str, body: str):
        preferences = booking.get(NOTIFICATION_PREFERENCES) or DEFAULT_NOTIFICATION_PREFERENCES
        channels = preferences.get(CHANNELS) or [CHANNEL_EMAIL]

        for channel in channels:
            strategy = self.strategies.get(channel)
            if not strategy:
                raise ValueError(f"Unsupported notification channel: {channel}")

            recipient = self._get_recipient(channel, booking, preferences)
            strategy.send_notification(recipient, subject, body)

    def _get_recipient(self, channel: str, booking: dict, preferences: dict):
        if channel == CHANNEL_EMAIL:
            return booking.get(USER_EMAIL)
        return preferences.get(TELEGRAM_CHAT_ID)
