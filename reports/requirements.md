# Fitness Class Management System

## Requirements Elicitation and Analysis

**Date of Client Meeting:** February 12, 2026  

**Elicitation Techniques Used:**  
- Direct questioning of the client regarding user roles, permissions, and workflows.  
- Simple booking flows to clarify overlaps and constraints.  
- Scenario-based questions to clarify system behavior (e.g., booking full classes, trainer privileges).  

**Reflection:**  
1. The combination of direct questioning and scenario sketches was very effective for understanding permissions and constraints, particularly around overlapping classes and trainer privileges.  
2. An important clarification gained: Guests cannot book classes, and trainers are allowed to join classes without consuming a member spot, which was not initially clear.  
---


## Requirements Specification

## A Flow Diagram (Manually Crafted)

```
                                    ┌──────────────────────────────────────────────────────────┐
                                    │         Fitness Class Management System                  │
                                    │                                                          │
         ┌─────┐                    │                                                          │
         │ o   │                    │          ┌─────────────────────┐                         │
         │/|\  │───────────────────────────────│  View Class List    │                         │
         │/ \  │  Guest             │          └─────────────────────┘                         │
         └─────┘                    │                                                          │
                                    │                                                          │
                                    │                                                          │
         ┌─────┐                    │          ┌─────────────────────┐                         │
         │ o   │───────────────────────────────│  View Class List    │                         │
         │/|\  │                    │          └─────────────────────┘                         │
         │/ \  │  Member            │                    │                                     │
         └─────┘                    │                    │                                     │
            │                       │          ┌─────────────────────┐                         │
            └──────────────────────────────────│   Book a Class      │                         │
                                    │          └─────────────────────┘                         │
                                    │                                                          │
                                    │                                                          │
         ┌─────┐                    │          ┌─────────────────────┐                         │
         │ o   │───────────────────────────────│  View Class List    │                         │
         │/|\  │                    │          └─────────────────────┘                         │
         │/ \  │  Trainer/          │                    │                                     │
         └─────┘  Admin             │          ┌─────────────────────┐                         │
            │──────────────────────────────────│   Create Class      │                         ┤
            │                       │          └─────────────────────┘                         │
            │                       │                    │                                     │
            │                       │          ┌─────────────────────┐                         │
            │──────────────────────────────────│   View Members      │                         │
            │                       │          └─────────────────────┘                         │
            │                       │                    │                                     │
            │                       │          ┌─────────────────────┐                         │
            └──────────────────────────────────│Send Reminder Emails │                         │
                                    │          └─────────────────────┘                         │
                                    │                                                          │
                                    └──────────────────────────────────────────────────────────┘
```

## Actors and Their Use Cases

**Guest (Not Registered)**
- View Class List

**Member (Registered)** 
- View Class List
- Book a Class

**Trainer/Admin**
- View Class List
- Create Class
- View Members
- Send Reminder Emails

## Use Cases

### Feature 1: Create Class (Trainer/Admin)

**Primary Actor:** Trainer/Admin  
**Goal:** Allow trainer/admin to create a new fitness class.

**Preconditions:**  
- User is authenticated as trainer/admin.

**Triggers:**  
- Trainer clicks "Create Class" button.

**Description:**  
1. Trainer/admin inputs the following details:  
   - Class Name/Title  
   - Date and Time  
   - Duration  
   - Capacity (>0)  
   - Location  
   - Description/Type  
2. System validates inputs:  
   - Class cannot be in the past.  
   - Trainer cannot create overlapping classes.  
3. Class is saved, visible to members and guests (guests see only upcoming classes).

**Postconditions:**  
- Class is created and listed in the system.

**Constraints:**  
- No editing or deleting classes in Sprint 1.  
- Only one trainer per class.

---

### Feature 2: View Class List (Guests and Members)

**Primary Actor:** Guest/Member  
**Goal:** Allow users to view available classes.

**Preconditions:**  
- None for guests; members must be authenticated.

**Description:**  
1. System displays upcoming classes only (past classes hidden).  
2. Each class shows:
   - Class ID
   - Class Name/Title  
   - Trainer Name
   - Date and Time  
   - Location  
   - Description/Type  
   - Remaining spots  
4. Optional filters for future sprints (location, trainer, time).

**Postconditions:**  
- Users can see the list of classes and details.

**Constraints:**  
- Viewing does not require login for guests.
- For future sprints, members will be able to view their bookings (previous and upcoming).

---

### Feature 3: Book a Class (Members Only)

**Primary Actor:** Member  
**Goal:** Book a slot in an upcoming class.

**Preconditions:**  
- Member is authenticated.  
- Class has available capacity.

**Description:**  
1. Member selects a class and clicks "Book".  
2. System checks capacity and trainer availability.  
3. If available, system books the member and immediately notifies them (e.g., alert).  
4. Trainers can join without taking a member spot.

**Postconditions:**  
- Booking is confirmed and visible in member’s upcoming classes.

**Constraints:**  
- No waitlist in Sprint 1.  
- No priority system beyond first-come-first-serve.  
- Users cannot cancel bookings in Sprint 1.

---

### Feature 4: View Members (Trainers Only)

**Primary Actor:** Trainer  
**Goal:** Allow trainer to view class roster.

**Preconditions:**  
- Trainer is authenticated.

**Description:**  
1. Trainer selects a class they created.  
2. System displays roster including:  
   - Member name  
   - Email (optional, depending on system design)  
   - Booking time

**Postconditions:**  
- Trainer can see the list of members for their classes.

**Constraints:**  
- Trainers can only view members for their own classes.  
- Members cannot view the roster.

---

### Feature 5: Email Reminders (Trainers Only)

**Primary Actor:** Trainer  
**Goal:** Allow trainer to send reminder emails to all registered members of a class.

**Preconditions:**  
- Trainer is authenticated.
- Trainer made the class.
- At least one member is booked in the class.

**Triggers:**  
- Trainer clicks "Send Reminder" button in the class.

**Description:**  
1. Trainer selects a class they created.  
2. System receives all registered members for the class.
3. If no members are registered, system returns a message: "No registered members to notify".
4. For each member, system sends an email that includes:
- Participant name
- Class name/title
- Class start and end date/time
- Class location
- Gym branding in the subject line (e.g., NYUAD GYM: Reminder for [Class Name])
5. Trainer receives a confirmation that reminders were sent successfully.

**Postconditions:**  
- All booked members receive a reminder email about the upcoming class.
- If sending fails for any email, the trainer is notified of the error.

**Constraints:**
- Only the assigned trainer can send reminders for a class.
- Trainer cannot send reminders for classes they are not assigned to.
- Emails are sent via AWS SES; both sender and recipients must be verified if in SES sandbox mode.