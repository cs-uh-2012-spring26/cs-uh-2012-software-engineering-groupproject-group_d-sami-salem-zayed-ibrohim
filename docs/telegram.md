# testing telegram notifications

## 1. env

```env
TELEGRAM_BOT_TOKEN="<shared_bot_token>"
TELEGRAM_BOT_USERNAME="sepr2bot"
TELEGRAM_BOT_POLLING_ENABLED="true"
```

no ngrok or webhook setup needed.

## 2. start app

local:

```bash
make run_local_server
```

docker:

```bash
docker compose up --build
```

## 3. create users

trainer:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"trainer_telegram@test.com","password":"password123","name":"telegram trainer","birthday":"1990-01-01","role":"trainer"}'
```

member:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"member_telegram@test.com","password":"password123","name":"telegram member","birthday":"2000-01-01","role":"member"}'
```

save both `access_token` values as `trainer_token` and `member_token`.

## 4. connect telegram

1. open `http://127.0.0.1:8000`
2. click **authorize**
3. paste `Bearer <member_token>`
4. click **connect to telegram**
5. press **start** in telegram

verify:

```bash
curl -X GET http://127.0.0.1:8000/notifications \
  -H "Authorization: Bearer <member_token>"
```

check for:

```json
"telegram_connected": true
```

## 5. enable telegram only

```bash
curl -X PATCH http://127.0.0.1:8000/notifications \
  -H "Authorization: Bearer <member_token>" \
  -H "Content-Type: application/json" \
  -d '{"channels":["telegram"]}'
```

## 6. create class

```bash
curl -X POST http://127.0.0.1:8000/classes \
  -H "Authorization: Bearer <trainer_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"telegram test yoga","start_date":"2027-12-01 10:00:00","end_date":"2027-12-01 11:00:00","capacity":10,"location":"studio a","description":"testing telegram reminders"}'
```

save returned `_id` as `class_id`.

## 7. book class

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer <member_token>" \
  -H "Content-Type: application/json" \
  -d '{"class_id":"<class_id>"}'
```

## 8. send reminder

```bash
curl -X POST http://127.0.0.1:8000/classes/<class_id>/reminder \
  -H "Authorization: Bearer <trainer_token>"
```

success:

```json
{"message":"Reminders sent successfully"}
```
