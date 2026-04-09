# Design Reflection Report
**CS-UH 2012 Software Engineering — Sprint 3A**
**Group D: Sami, Salem, Zayed, Ibrohim**

## Task 2: Reflection on Design Principles

We manually reviewed the codebase and found five examples where design principles are either violated or correctly applied, covering five distinct principles.

### 1. Abstraction — Violation

**File:** `app/apis/classes.py`
**Method:** `Classes.post()`
**Lines:** 52–126

**What abstraction means:**
The caller should not need to know the internal steps of a function. It should just call one method and get a result. All the complexity should be hidden inside a service.

**What we found:**
The `post()` method that creates a class does everything itself. There is no service hiding the complexity. The three screenshots below show the three parts of this method:

**Screenshot 1** — Role check and reading input from the request (lines 52–61):
![Role check — lines 52–61](images/abstraction_1_role_check.png)

**Screenshot 2** — Validating the input data (lines 63–94):
![Input parsing and validation — lines 63–94](images/abstraction_2_validation.png)

**Screenshot 3** — Looking up the trainer in the database and creating the class (lines 96–126):
![Database lookup and class creation — lines 96–126](images/abstraction_3_db_and_create.png)

**Why this is a problem:**
As seen in Screenshots 1, 2, and 3, the endpoint method itself handles all of these steps: checking the user's role, reading and parsing the request body, validating all input fields, parsing and checking dates, looking up the trainer in the database, checking for scheduling conflicts, and creating the class. That is seven different things in one method.

Now compare that to the reminder endpoint in the same file (lines 256–260):

```python
reminder_service = ReminderService(SESEmailService(Config.SES_SENDER_EMAIL))
return reminder_service.send_reminder(class_id, trainer_id)
```

That is two lines. Everything happens inside `ReminderService` and the endpoint does not need to know how. The create-class endpoint does not have an equivalent service, so it violates abstraction.

### 2. Encapsulation — Violation

**File:** `app/apis/classes.py`
**Method:** `Classes.get()`
**Lines:** 158–167

**What encapsulation means:**
Internal data should stay private inside its class. Other parts of the code should interact through methods, not by directly touching internal fields or data structures.

**What we found:**
The `get()` method that returns upcoming classes directly reads field names from the raw database response inside the API layer. Screenshot 4 shows this:

**Screenshot 4** — API directly accessing raw database fields (lines 144–170):
![Direct access to raw DB fields](images/encapsulation_raw_fields.png)

**Why this is a problem:**
As seen in Screenshot 4, the API uses strings like `"_id"` and `"trainer_name"` to access data directly:

```python
result.append({
    "_id": cls.get("_id"),
    "trainer_name": cls.get("trainer_name"),
    ...
})
```

The API now knows how data is stored inside the database. If we ever rename `"trainer_name"` to `"instructor_name"` in the database, every file that uses that string will break. The fix would be to have `ClassResource` provide a method that formats the response internally, so the API never needs to know the field names.

### 3. Modularity — Violation (Low Cohesion)

**File:** `app/apis/classes.py`
**Lines:** 1–261 (entire file)

**What modularity means:**
A file should do one clear thing. Everything in it should belong together. This is called high cohesion. If a file does many unrelated things, it has low cohesion.

**What we found:**
This one file contains three completely different resources. Screenshots 5, 6, and 7 show each one:

**Screenshot 5** — First resource: `Classes` (creates and views classes, line 44):
![First resource: Classes](images/modularity_1_first_class.png)

**Screenshot 6** — Second resource: `ClassMembers` (views who booked a class, line 175):
![Second resource: ClassMembers](images/modularity_2_second_class.png)

**Screenshot 7** — Third resource: `ClassReminder` with imports placed in the middle of the file (lines 228–235):
![Mid-file imports and third resource](images/modularity_3_imports_and_third_class.png)

**Why this is a problem:**
As seen across Screenshots 5, 6, and 7, `Classes` handles creating and viewing classes, `ClassMembers` handles viewing who booked a class, and `ClassReminder` handles sending reminder emails which has nothing to do with the other two. Also in Screenshot 7, the imports for `ReminderService` and `SESEmailService` appear in the middle of the file at lines 229–230 instead of at the top where all imports should go. This shows `ClassReminder` was added later without restructuring the file. The fix would be to split this into three separate files, one per resource.

### 4. Single Responsibility Principle — Violation

**File:** `app/apis/auth.py`
**Method:** `Register.post()`
**Lines:** 35–73

**What SRP means:**
A method should have one job and one reason to change. If you need to update a method because the validation rules changed, AND because the database changed, AND because the token format changed — it has too many responsibilities.

**What we found:**
The `Register.post()` method does many different things at once. Screenshots 8 and 9 show the two halves:

**Screenshot 8** — Input reading, a debug log, and validation (lines 35–56):
![Input parsing, debug log, and validation](images/srp_1_input_and_validation.png)

**Screenshot 9** — Creating the user, generating a token, and returning the response (lines 57–73):
![DB creation, token generation, and response](images/srp_2_db_token_response.png)

**Why this is a problem:**
As seen in Screenshots 8 and 9, this one method is responsible for reading input from the request, validating required fields and the role value, checking if the user already exists in the database, creating the user, handling MongoDB-specific errors, generating a JWT token, and building the response. Screenshot 8 also shows a `print()` debug statement left in production code on line 44, which does not belong here. This method has at least five different reasons to change, which directly violates SRP.

### 5. Open/Closed Principle — Good Example

**Files:** `app/services/email_service.py` (Lines: 1–4, Method: `send_email`) and `app/services/ses_email_service.py` (Lines: 1–24, Method: `send_email`)

**What OCP means:**
A class should be open for extension (you can add new behavior) but closed for modification (you do not touch existing working code). You do this by creating a base class that others can extend.

**What we found:**
The email service design correctly follows this principle. Screenshots 10 and 11 show the two files:

**Screenshot 10** — The base class `EmailService` (email_service.py):
![Base class EmailService](images/ocp_1_email_service.png)

**Screenshot 11** — The concrete implementation `SESEmailService` (ses_email_service.py):
![Concrete extension SESEmailService](images/ocp_2_ses_service.png)

**Why this is correct:**
As seen in Screenshot 10, `EmailService` just defines what `send_email` should look like. It never needs to change. Screenshot 11 shows `SESEmailService` implementing it for AWS without touching the base class.

When Sprint 3B adds Telegram or SMS notifications (Feature 7), the team can simply write:

```python
class TelegramService(EmailService):
    def send_email(self, recipient, subject, body):
        # send via Telegram
```

No existing code needs to be modified. `ReminderService` will work with the new class automatically because it depends on `EmailService` in general, not on `SESEmailService` specifically.
