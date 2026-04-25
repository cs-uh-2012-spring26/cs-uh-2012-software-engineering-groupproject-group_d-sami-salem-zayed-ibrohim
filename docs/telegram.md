# Testing Feature 7: Telegram Notifications

Use this guide to test Telegram reminders. I have set up a toy bot, but you can always create your own bot and use token for that bot.

## 1. Configure the Bot Token

1. Create your own bot using https://t.me/BotFather
2. Start the bot from your account! Very important, without this the bot will not be able to send any messages to you.
3. After configuring a new bot, BotFather will provide you with API key to the bot. 
4. Paste it to the  `.env` file as shown below

Set the bot token locally in `.env`:

```env
TELEGRAM_BOT_TOKEN="<your_token>"
```

## 2. Get Your Telegram Chat ID

1. Open https://t.me/userinfobot
2. Start the bot.
3. Copy the numeric `id` it returns.

Use that value as your `telegram_chat_id`.

## 3. Start the App

```bash
make run_local_server
```

The API should be available at `http://127.0.0.1:8000`.

## 4. Create Test Users

Register a trainer and copy the returned `access_token` as `TRAINER_TOKEN`:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"trainer_telegram@test.com","password":"password123","name":"Telegram Trainer","birthday":"1990-01-01","role":"trainer"}'
```

On a new terminal, register a member and copy the returned `access_token` as `MEMBER_TOKEN`:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"member_telegramm@test.com","password":"password123","name":"Telegram Member","birthday":"2000-01-01","role":"member"}'
```

## 5. Create and Book a Future Class

Use the trainer token to create a future class. Copy the returned `_id` as `CLASS_ID`.

```bash
curl -X POST http://127.0.0.1:8000/classes \
  -H "Authorization: Bearer <TRAINER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Telegram Test Yoga","start_date":"2026-12-01 10:00:00","end_date":"2026-12-01 11:00:00","capacity":10,"location":"Studio A","description":"Testing Telegram reminders"}'
```

Use the member token to book the class. Copy the returned `booking_id` as `BOOKING_ID`.

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer <MEMBER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"class_id":"<CLASS_ID>"}'
```

## 6. Enable Telegram for the Booking

```bash
curl -X PATCH http://127.0.0.1:8000/bookings/<BOOKING_ID>/notifications \
  -H "Authorization: Bearer <MEMBER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"channels":["telegram"],"telegram_chat_id":"<YOUR_CHAT_ID>"}'
```

Expected response:

```json
{
  "message": "Notification preferences updated successfully",
  "booking_id": "...",
  "notification_preferences": {
    "channels": ["telegram"],
    "telegram_chat_id": "..."
  }
}
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