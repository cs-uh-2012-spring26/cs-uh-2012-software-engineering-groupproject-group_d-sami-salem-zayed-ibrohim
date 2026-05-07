# Testing Feature 7: Telegram Notifications

Use this guide to test Telegram reminders with the shared app bot. Members should not create a bot or manually copy a chat id.

## 1. Configure Telegram

Set the shared bot token in `.env`. The bot username defaults to `sepr2bot`, but you can override it if needed.

```env
TELEGRAM_BOT_TOKEN="<shared_bot_token>"
TELEGRAM_BOT_USERNAME="sepr2bot"
TELEGRAM_BOT_POLLING_ENABLED="true"
```

The app now uses Telegram long polling. Local testing does not require ngrok or `setWebhook`; when polling starts, the app clears any old webhook so `getUpdates` can receive bot messages.

## 2. Start the App

```bash
make run_local_server
```

The API should be available at `http://127.0.0.1:8000`.

## 3. Create Test Users

Register a trainer and copy the returned `access_token` as `TRAINER_TOKEN`:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"trainer_telegram@test.com","password":"password123","name":"Telegram Trainer","birthday":"1990-01-01","role":"trainer"}'
```

Register a member and copy the returned `access_token` as `MEMBER_TOKEN`:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"member_telegram@test.com","password":"password123","name":"Telegram Member","birthday":"2000-01-01","role":"member"}'
```

## 4. Link Telegram

In Swagger, click **Authorize** and paste the member token as `Bearer <MEMBER_TOKEN>`.

Click **connect to telegram** next to the authorize button. Swagger calls `/notifications`, gets a user-specific `telegram_launch_url`, and opens Telegram.

Press **Start** in Telegram. The running app polls Telegram, receives `/start <user_token>`, stores your Telegram `chat.id`, and sends a confirmation message in the bot chat.

To confirm the app stored the chat id:

```bash
curl -X GET http://127.0.0.1:8000/notifications \
  -H "Authorization: Bearer <MEMBER_TOKEN>"
```

Expected:

```json
{
  "notification_preferences": {
    "channels": ["email"]
  },
  "telegram_connected": true,
  "telegram_launch_url": "https://t.me/sepr2bot?start=<user_token>"
}
```

## 5. Enable Telegram Notifications

```bash
curl -X PATCH http://127.0.0.1:8000/notifications \
  -H "Authorization: Bearer <MEMBER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"channels":["email","telegram"]}'
```

Expected response:

```json
{
  "message": "Notification preferences updated successfully",
  "notification_preferences": {
    "channels": ["email", "telegram"]
  },
  "telegram_connected": true,
  "telegram_launch_url": "https://t.me/sepr2bot?start=<user_token>"
}
```

## 6. Create and Book a Future Class

Use the trainer token to create a future class. Copy the returned `_id` as `CLASS_ID`.

```bash
curl -X POST http://127.0.0.1:8000/classes \
  -H "Authorization: Bearer <TRAINER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Telegram Test Yoga","start_date":"2026-12-01 10:00:00","end_date":"2026-12-01 11:00:00","capacity":10,"location":"Studio A","description":"Testing Telegram reminders"}'
```

Use the member token to book the class:

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer <MEMBER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"class_id":"<CLASS_ID>"}'
```

## 7. Send the Reminder

```bash
curl -X POST http://127.0.0.1:8000/classes/<CLASS_ID>/reminder \
  -H "Authorization: Bearer <TRAINER_TOKEN>"
```

Expected API response:

```json
{
  "message": "Reminders sent successfully"
}
```

You should receive the reminder message in Telegram.
