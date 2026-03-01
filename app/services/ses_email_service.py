import boto3
from botocore.exceptions import ClientError
from app.services.email_service import EmailService

# SES (Simple Email Service) implementation of a generic EmailService. Can be reused for other services later on.
class SESEmailService(EmailService):

    def __init__(self, sender_email, region="us-east-1"):
        self.sender_email = sender_email
        self.client = boto3.client("ses", region_name=region)

    # Send an Email using AWS SES
    def send_email(self, recipient, subject, body):
        try:
            self.client.send_email(
                Source=self.sender_email,
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": body}},
                },
            )
        except ClientError as e:
            raise Exception(e.response["Error"]["Message"])