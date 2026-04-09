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

1. long method: post in [app/apis/classes.py](../app/apis/classes.py#L52) is a long method because it handles auth, validation, parsing, overlap checks, persistence, and response formatting in one block.  
  image: [code_smell_1.png](images/code_smell_1.png)

2. dead code: jwt = jwtmanager(app) in [app/__init__.py](../app/__init__.py#L19) is created but never used after assignment.
  image: [code_smell_2.png](images/code_smell_2.png)

3. primitive obsession: date and time are parsed as raw strings [app/apis/classes.py](../app/apis/classes.py#L82). Better to take the DateRange into separate class with its own methods (overlap checking, past validation) and attributes (start time, end time).
  image: [code_smell_3.png](images/code_smell_3.png)

4. long parameter list: create_class in [app/db/classes.py](../app/db/classes.py#L26) has a long parameter list because it takes 8 inputs: title, trainer_id, trainer_name, start_date, end_date, capacity, location, and description.  
  image: [code_smell_4.png](images/code_smell_4.png)

5. duplicate code: getting jwt claims all repeat the same pattern in different places.
- a. [app/apis/classes.py](../app/apis/classes.py#L54)
- b. [app/apis/classes.py](../app/apis/classes.py#L184)
- c. [app/apis/booking.py](../app/apis/booking.py#L39)


  images: 
  1. [code_smell_5a.png](images/code_smell_5a.png)
  2. [code_smell_5b.png](images/code_smell_5b.png)
  3. [code_smell_5c.png](images/code_smell_5c.png)

# Reflection on current design: pros and cons (Task 4)