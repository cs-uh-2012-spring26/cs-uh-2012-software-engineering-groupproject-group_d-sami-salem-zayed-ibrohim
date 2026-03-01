# Is a Base Class. It allows the use of multiple Email Services and is useful for testing
class EmailService:
    def send_email(self, to: str, subject: str, body: str):
        raise NotImplementedError