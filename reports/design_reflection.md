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

- dead code: jwt = jwtmanager(app) in [app/__init__.py](../app/__init__.py#L19) is created but never used after assignment.
  image: [code_smell_2.png](images/code_smell_2.png)

- primitive obsession: date and time are parsed as raw strings [app/apis/classes.py](../app/apis/classes.py#L82).
  image: [code_smell_3.png](images/code_smell_3.png)

- long parameter list: create_class in [app/db/classes.py](../app/db/classes.py#L26) has a long parameter list because it takes 8 inputs: title, trainer_id, trainer_name, start_date, end_date, capacity, location, and description.  
  image: [code_smell_4.png](images/code_smell_4.png)

- long parameter list: create_user in [app/db/users.py](../app/db/users.py#L27) has a long parameter list because it takes 5 inputs: email, password, name, birthday, and role.  
  image: [code_smell_5.png](images/code_smell_5.png)

# Reflection on current design: pros and cons (Task 4)