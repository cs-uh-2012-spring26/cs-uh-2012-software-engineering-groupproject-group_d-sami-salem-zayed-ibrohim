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
    trainer_email = get_jwt_identity()
    role = get_jwt().get("role")
    data = request.json
    return ClassService().create_class(trainer_email, role, data)
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

[To be added by Ibrohim]

---

## 2. Design Patterns Used

[To be added]

---

## 3. Updated Class Diagram

[To be added by Zayed]

---

## 4. Team Responsibilities

[To be added]
