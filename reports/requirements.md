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
            └──────────────────────────────────│   View Members      │                         │
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
   - Name/Title  
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
   - Name/Title  
   - Trainer  
   - Date and Time  
   - Location  
   - Description/Type  
   - Capacity/Remaining spots  
3. Optional filters for future sprints (location, trainer, time).

**Postconditions:**  
- Users can see the list of classes and details.

**Constraints:**  
- Viewing does not require login for guests, but members can see their bookings.

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
