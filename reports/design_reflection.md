# Executive summary

## Tools used

## Manual analysis done:

## Team member responsibilies:

- Task 1: Zayed
- Task 2: Salem
- Task 3: Ibrohim
- Task 4: Sami

# Design Diagrams (Task 1)

# Written analysis of reflection of design principles (Task 2)

# Code smells (Task 3)

- long method: post in [app/apis/classes.py](../app/apis/classes.py#L44) is a long method because it handles auth, validation, parsing, overlap checks, persistence, and response formatting in one block.  
  image: [code_smell_1.png](images/code_smell_1.png)

- long method: post in [app/apis/booking.py](../app/apis/booking.py#L28) is a long method because it combines jwt checks, request parsing, booking rules, user lookup, and insert logic.  
  image: [code_smell_2.png](images/code_smell_2.png)

- long method: send_reminder in [app/services/reminder_service.py](../app/services/reminder_service.py#L5) is a long method because it does class lookup, ownership validation, end-date checking, booking retrieval, email body construction, and sending.  
  image: [code_smell_3.png](images/code_smell_3.png)

- long parameter list: create_class in [app/db/classes.py](../app/db/classes.py#L26) has a long parameter list because it takes 8 inputs: title, trainer_id, trainer_name, start_date, end_date, capacity, location, and description.  
  image: [code_smell_4.png](images/code_smell_4.png)

- long parameter list: create_user in [app/db/users.py](../app/db/users.py#L27) has a long parameter list because it takes 5 inputs: email, password, name, birthday, and role.  
  image: [code_smell_5.png](images/code_smell_5.png)

# Reflection on current design: pros and cons (Task 4)