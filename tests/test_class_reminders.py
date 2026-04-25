import pytest
from unittest.mock import patch, ANY
from http import HTTPStatus

# Mock external services so we don't send real emails/telegrams during tests
@patch("app.services.ses_email_service.SESEmailService.send_notification")
@patch("app.services.telegram_notification_service.TelegramNotificationService.send_notification")
def test_reminder_integration_and_dispatch(mock_tele, mock_email, client, trainer_token, sample_bookings_with_prefs):
    # Triggers the reminder workflow for a class with mixed preferences
    class_id = sample_bookings_with_prefs["class_id"]
    resp = client.post(f"/classes/{class_id}/reminder", headers={"Authorization": f"Bearer {trainer_token}"})

    assert resp.status_code == HTTPStatus.OK
    # Ensure Alice and Bob both get emails, but only Bob gets a Telegram
    assert mock_email.call_count == 2
    assert mock_tele.call_count == 1
    mock_tele.assert_called_with("12345", ANY, ANY)

# Verify that only the class owner (trainer) can send reminders
def test_reminder_trainer_permissions(client, other_trainer_token, sample_class):
    resp = client.post(f"/classes/{sample_class}/reminder", headers={"Authorization": f"Bearer {other_trainer_token}"})
    assert resp.status_code == HTTPStatus.FORBIDDEN