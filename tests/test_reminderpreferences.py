import pytest
from http import HTTPStatus
from app.db.bookings import CHANNEL_EMAIL, CHANNEL_TELEGRAM, CHANNELS, TELEGRAM_CHAT_ID

# Happy path: Member successfully opts into Telegram
def test_update_preferences_success(client, member_token, sample_booking):
    payload = {CHANNELS: [CHANNEL_EMAIL, CHANNEL_TELEGRAM], TELEGRAM_CHAT_ID: "12345"}
    resp = client.patch(f"/bookings/{sample_booking}/notifications", 
                        json=payload, headers={"Authorization": f"Bearer {member_token}"})
    
    assert resp.status_code == HTTPStatus.OK
    assert CHANNEL_TELEGRAM in resp.json["notification_preferences"][CHANNELS]

# Validation path: Rejects invalid channels and missing IDs
def test_preferences_validation_logic(client, member_token, sample_booking):
    # Block unknown channels like 'sms'
    resp = client.patch(f"/bookings/{sample_booking}/notifications",
                        json={CHANNELS: ["sms"]}, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    # Block Telegram if no Chat ID is provided
    resp = client.patch(f"/bookings/{sample_booking}/notifications",
                        json={CHANNELS: [CHANNEL_TELEGRAM]}, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == HTTPStatus.BAD_REQUEST

# Security path: Prevent users from editing someone else's booking
def test_preferences_authorization(client, other_member_token, sample_booking):
    resp = client.patch(f"/bookings/{sample_booking}/notifications",
                        json={CHANNELS: [CHANNEL_EMAIL]}, headers={"Authorization": f"Bearer {other_member_token}"})
    assert resp.status_code == HTTPStatus.FORBIDDEN