from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

from app.db.users import CHANNEL_EMAIL, CHANNEL_TELEGRAM, CHANNELS
from app.services.telegram_bot_polling_service import TelegramBotPollingService


def test_update_preferences_success(client, member_token):
    payload = {CHANNELS: [CHANNEL_EMAIL, CHANNEL_TELEGRAM]}
    resp = client.patch("/notifications",
                        json=payload, headers={"Authorization": f"Bearer {member_token}"})
    
    assert resp.status_code == HTTPStatus.OK
    assert CHANNEL_TELEGRAM in resp.json["notification_preferences"][CHANNELS]
    assert resp.json["telegram_launch_url"].startswith("https://t.me/sepr2bot?start=")


def test_preferences_validation_logic(client, member_token):
    # Block unknown channels like 'sms'
    resp = client.patch("/notifications",
                        json={CHANNELS: ["sms"]}, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    # Telegram no longer requires users to manually provide a chat id.
    resp = client.patch("/notifications",
                        json={CHANNELS: [CHANNEL_TELEGRAM]}, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == HTTPStatus.OK


def test_preferences_authorization(client, trainer_token):
    resp = client.patch("/notifications",
                        json={CHANNELS: [CHANNEL_EMAIL]}, headers={"Authorization": f"Bearer {trainer_token}"})
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_telegram_webhook_connects_chat_id(client, member_token):
    settings_resp = client.get("/notifications", headers={"Authorization": f"Bearer {member_token}"})
    launch_url = settings_resp.json["telegram_launch_url"]
    token = parse_qs(urlparse(launch_url).query)["start"][0]

    webhook_resp = client.post("/telegram/webhook", json={
        "message": {
            "text": f"/start {token}",
            "chat": {"id": 12345},
        }
    })
    assert webhook_resp.status_code == HTTPStatus.OK

    refreshed_resp = client.get("/notifications", headers={"Authorization": f"Bearer {member_token}"})
    assert refreshed_resp.json["telegram_connected"] is True


def test_telegram_polling_update_connects_chat_id(client, app, member_token, monkeypatch):
    settings_resp = client.get("/notifications", headers={"Authorization": f"Bearer {member_token}"})
    token = parse_qs(urlparse(settings_resp.json["telegram_launch_url"]).query)["start"][0]
    sent_messages = []

    service = TelegramBotPollingService(app, bot_token="test-bot-token", poll_timeout=1)
    monkeypatch.setattr(
        service,
        "_send_message",
        lambda chat_id, text: sent_messages.append({"chat_id": chat_id, "text": text}),
    )

    service.process_update({
        "update_id": 1,
        "message": {
            "text": f"/start {token}",
            "chat": {"id": 12345},
        },
    })

    refreshed_resp = client.get("/notifications", headers={"Authorization": f"Bearer {member_token}"})
    assert refreshed_resp.json["telegram_connected"] is True
    assert sent_messages == [{
        "chat_id": 12345,
        "text": "telegram connected. you can now receive class reminders here.",
    }]


def test_telegram_webhook_rejects_empty_body(client):
    resp = client.post("/telegram/webhook")
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "required" in resp.json["message"]


def test_telegram_webhook_hidden_from_swagger(client):
    spec = client.get("/swagger.json").get_json()
    assert "/telegram/webhook" not in spec["paths"]


def test_old_booking_notification_endpoint_removed(client, member_token, sample_booking):
    resp = client.patch(f"/bookings/{sample_booking}/notifications",
                        json={CHANNELS: [CHANNEL_EMAIL]}, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == HTTPStatus.NOT_FOUND
