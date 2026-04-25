# Sprint 3B — Redesign Report

---

## 1. How We Fixed Each Violated Design Principle and Code Smell

### Abstraction Violation

**What was wrong:**
`Classes.post()` in `app/apis/classes.py` was a 75-line route handler that did everything itself: role checking, input parsing, field validation, date parsing, date validation, database lookup, overlap checking, and class creation. The route handler knew every internal step, which means there was no abstraction hiding the complexity.

**How we fixed it:**
We created `app/services/class_service.py` containing a `ClassService` class. All 8 steps moved into `ClassService.create_class()`. The route handler now only collects the request data and delegates to the service:

```python
def post(self):
    auth_user = get_authenticated_user()
    data = request.json
    return ClassService().create_class(auth_user.email, auth_user.role, data)
```

The same violation existed in `booking.py` (`Bookings.post()` and `MyBookedClasses.get()`) and `class_members_resource.py` (`ClassMembers.get()`). We fixed those by extracting `BookingService` and `ClassMembersService` using the same approach.

**New structure:**
`app/services/class_service.py`, `app/services/booking_service.py`, `app/services/class_members_service.py`

---

### Encapsulation Violation

**What was wrong:**
`Classes.get()` in `app/apis/classes.py` was directly reading raw database field names as strings inside the API layer:

```python
result.append({
    "_id": cls.get("_id"),
    "trainer_name": cls.get("trainer_name"),
    ...
})
```

The API layer depended on internal database details it should not know about. The same issue existed in `booking.py`. If any field name changed in the database, every file using those strings would break.

**How we fixed it:**
We added a `to_dict()` method to `ClassResource` in `app/db/classes.py`. This is now the only place in the codebase that knows the database field names. The API calls:

```python
result.append(class_resource.to_dict(cls, remaining_spots))
```

The API no longer touches any raw field names. Any future field rename only requires updating `to_dict()`.

**New structure:**
`to_dict()` method added to `app/db/classes.py`

---

### Modularity Violation

**What was wrong:**
`app/apis/classes.py` contained three completely unrelated resources in one 261-line file: `Classes` (creating and listing classes), `ClassMembers` (viewing who booked a class), and `ClassReminder` (sending reminder emails). The imports for `ReminderService` and `SESEmailService` also appeared in the middle of the file at line 229 instead of the top, showing that `ClassReminder` was added later without proper restructuring.

**How we fixed it:**
We deleted `classes.py` and split it into three focused files.

`app/apis/class_resource.py` handles creating and listing classes only.
`app/apis/class_members_resource.py` handles viewing class members only.
`app/apis/class_reminder_resource.py` handles sending reminders only, with all imports placed at the top of the file.

Each file now has one clear responsibility. Changing reminder logic only requires opening one small file.

**New structure:**
`app/apis/class_resource.py`, `app/apis/class_members_resource.py`, `app/apis/class_reminder_resource.py`

---

### Single Responsibility Principle Violation

**What was wrong:**
`Register.post()` in `app/apis/auth.py` had 8 different responsibilities in one method: reading the request body, validating required fields, validating the role value, checking if the user already exists, creating the user, handling MongoDB duplicate key errors, generating a JWT token, and building the response. There was also a `print()` debug statement on line 44 that was printing user registration data including passwords to the server terminal.

**How we fixed it:**
We created `app/services/auth_service.py` containing an `AuthService` class. All logic moved into `AuthService.register_user()`. The debug print statement was removed. The route handler became:

```python
def post(self):
    data = request.json
    return AuthService().register_user(data)
```

The method now has one reason to change. If validation rules change, only `AuthService` is updated. If the JWT format changes, only `AuthService` is updated.

**New structure:**
`app/services/auth_service.py`

---

### Overall Architectural Change

All four fixes follow the same pattern. The codebase now has three clean layers:

```
app/apis/       receives HTTP request, calls service, returns response
app/services/   contains all business logic and validation
app/db/         talks to MongoDB only
```

Before the refactoring, the `apis/` layer mixed all three responsibilities. After the refactoring, each layer does only its own job and the route handlers are 3 to 6 lines each.

---

### Code Smell Fixes

#### 1. Long Method

**What was wrong:**
The Sprint 3A report identified `Classes.post()` in `app/apis/classes.py` as a long method because it mixed authentication, request parsing, validation, date parsing, conflict checking, persistence, and response formatting in one route handler.

**How we fixed it:**
This smell was removed as part of the abstraction refactor above. The logic now lives in `ClassService.create_class()`, while the route in `app/apis/class_resource.py` is only a thin controller that reads the request and delegates to the service.

**New structure:**
`app/apis/class_resource.py`, `app/services/class_service.py`

#### 2. Dead Code

**What was wrong:**
Sprint 3A identified `jwt = JWTManager(app)` in `app/__init__.py` as dead code because the assignment was never used after initialization.

**How we fixed it:**
We removed the unused variable and kept only the required side effect:

```python
JWTManager(app)
```

This keeps the JWT extension initialized without leaving misleading unused state behind.

**New structure:**
`app/__init__.py`

#### 3. Primitive Obsession

**What was wrong:**
The class-creation flow handled start and end times as raw strings and repeatedly parsed them with `datetime.strptime(...)`. This scattered date rules across the service logic and made validation harder to reuse.

**How we fixed it:**
We introduced two small value objects in `app/services/class_models.py`:

- `ClassSchedule` owns date parsing and temporal validation.
- `CreateClassRequest` owns request validation and converts the raw payload into typed data.

`ClassService.create_class()` now works with those objects instead of manually juggling primitive date strings. We also reused `ClassSchedule.parse_datetime()` inside `ReminderService` so date parsing is centralized in one place.

**New structure:**
`app/services/class_models.py`, `app/services/class_service.py`, `app/services/reminder_service.py`

#### 4. Long Parameter List

**What was wrong:**
Sprint 3A flagged `ClassResource.create_class(...)` in `app/db/classes.py` because it required eight separate parameters: title, trainer_id, trainer_name, start_date, end_date, capacity, location, and description.

**How we fixed it:**
We changed the database method to accept a single payload object or mapping:

```python
def create_class(self, class_data=None, **legacy_fields):
    fitness_class = self._normalize_class_data(class_data, legacy_fields)
    result = self.collection.insert_one(fitness_class)
```

The service now passes a `ClassRecord` object created from the validated request data. This keeps the method signature short and makes it easier to evolve the stored class shape later.

**New structure:**
`app/db/classes.py`, `app/services/class_models.py`, `app/services/class_service.py`

#### 5. Duplicate Code

**What was wrong:**
Sprint 3A identified repeated JWT-claim extraction logic across multiple route handlers in `classes.py` and `booking.py`. The same pattern was later still present across `class_resource.py`, `booking.py`, `class_members_resource.py`, and `class_reminder_resource.py`.

**How we fixed it:**
We introduced a shared helper in `app/services/auth_context.py`:

```python
auth_user = get_authenticated_user()
```

This returns one `AuthenticatedUser` object containing `user_id`, `role`, and `email`. Protected routes now use that helper instead of manually calling `get_jwt()` and `get_jwt_identity()` in each file. We also moved `Login.post()` behind `AuthService.login_user()` so the auth endpoints follow the same thin-route design.

**New structure:**
`app/services/auth_context.py`, `app/apis/class_resource.py`, `app/apis/booking.py`, `app/apis/class_members_resource.py`, `app/apis/class_reminder_resource.py`, `app/apis/auth.py`, `app/services/auth_service.py`

---

## 2. Design Patterns Used

### Strategy Pattern for Notifications

Feature 7 requires the system to support email and Telegram now, while also making it easy to add future channels such as SMS or WhatsApp later. That means the reminder workflow should not depend directly on one concrete delivery mechanism.

We used the Strategy pattern for notification delivery:

- `NotificationService` defines the common `send_notification(...)` interface.
- `EmailService` adapts email-specific behavior to that generic notification interface.
- `SESEmailService` is a concrete strategy that sends notifications through AWS SES.
- `TelegramNotificationService` is a concrete strategy that sends notifications through the Telegram Bot API.
- `NotificationDispatcher` maps selected channel names to strategy objects.
- `ReminderService` depends on the dispatcher and does not know which concrete delivery strategy is being used.

This gives us two important benefits:

1. `ReminderService` is closed for modification when a new notification channel is added.
2. New channels can be introduced by creating another implementation, for example `SmsNotificationService`, and registering it with the dispatcher without rewriting the reminder workflow.

In other words, the redesign now follows the extensibility requirement from Sprint 3B: adding a new notification channel means adding a new strategy class and one dispatcher registration instead of editing reminder business logic.

### Feature 7: Per-Booking Notification Preferences

Feature 7 is implemented at the booking level because the requirement says the user is already registered in a class. Each booking now stores `notification_preferences`, with email-only as the default for backward compatibility:

```json
{
  "channels": ["email"],
  "telegram_chat_id": null
}
```

Members can update their own booking preferences through `PATCH /bookings/<booking_id>/notifications`. The endpoint rejects empty channel lists, unsupported channel names, Telegram preferences without a `telegram_chat_id`, non-member requests, and attempts to update another member's booking.

When a trainer calls `POST /classes/<class_id>/reminder`, `ReminderService` retrieves all bookings and sends each reminder through the channels selected on that booking. Existing bookings without preferences still receive email reminders, so older data remains compatible with the new design.

### Value Objects for Class Creation

We also introduced `ClassSchedule` and `CreateClassRequest` as value objects for the class-creation flow. These objects centralize validation and date handling, which makes the code easier to maintain as recurring classes are added in Feature 6.

Although the main GoF pattern used here is Strategy, these value objects were an important supporting refactor because they removed primitive date handling from the route/service logic and gave us a cleaner foundation for future schedule-related behavior.

---

## 3. Updated Class Diagram

<img width="7992" height="6204" alt="SoftwareEngineering_ClassDiagram_Sprint3B-Copy of Copy of Copy of Copy of Copy of Copy of Copy of FormattedandDataTypeDefinedSprint3B drawio" src="https://github.com/user-attachments/assets/a46a4f30-dca4-4429-b2cd-fea30670ccdd" />

---

## 4. Team Responsibilities

- Task 1 Ibrohim and Salem
- Task 2:
  - ⁠Sami - Feature 6
  - ⁠⁠Ibrohim - Feature 7
- Task 3:
  - ⁠Sami - Feature 6
  - ⁠⁠Zayed - Feature 7
- Task 4 Ibrohim
- Task 5:
  - ⁠Zayed + someone to review - Diagram update
  - ⁠⁠Ibrohim + Sami + Salem - Documentation
