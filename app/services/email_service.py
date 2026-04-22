from app.services.notification_service import NotificationService


# base email implementation for pluggable notification delivery strategies
class EmailService(NotificationService):
    def send_notification(self, recipient: str, subject: str, body: str):
        self.send_email(recipient, subject, body)

    def send_email(self, to: str, subject: str, body: str):
        raise NotImplementedError