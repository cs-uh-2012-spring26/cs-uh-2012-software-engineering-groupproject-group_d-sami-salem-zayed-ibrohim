[![CI Workflow for Testing](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group_d-sami-salem-zayed-ibrohim/actions/workflows/tests.yml/badge.svg)](https://github.com/cs-uh-2012-spring26/cs-uh-2012-software-engineering-groupproject-group_d-sami-salem-zayed-ibrohim/actions/workflows/tests.yml)
# Fitness Class Management System

A Flask REST API server for managing fitness classes, bookings, and user authentication. The system supports three user types: guests (view classes), members (view and book classes), and trainers (create classes and view member rosters).

## Prerequisites

- python 3.10 or higher
- MongoDB installed. Follow [https://www.mongodb.com/docs/manual/installation/](https://www.mongodb.com/docs/manual/installation/)
to install MongoDB locally. Select the right link for your operating system.

## Tech Stack

This flask web app uses:

- [Flask-RESTX][flask-restx] for creating REST APIs. Directory structure
follows [flask restx instructions on scaling your project][flask-restx-scaling]
  - flask-restx automatically generates
  [OpenAPI specifications][openapi-specification] for your API
- [PyMongo][pymongo] for communicating with the mongodb database
- [pytest][pytest] for testing
(see [flask specific testing instructions on pytest][pytest-flask]
for more info specific to testing Flask applications)
- [mongomock][mongomock] for mocking the mongodb during unit testing

[flask-restx]: https://flask-restx.readthedocs.io/en/latest/quickstart.html
[flask-restx-scaling]: https://flask-restx.readthedocs.io/en/latest/scaling.html
[openapi-specification]: https://swagger.io/docs/specification/v3_0/about/
[pymongo]: https://pymongo.readthedocs.io/en/stable/
[pytest]: https://docs.pytest.org/en/stable/
[pytest-flask]: https://flask.palletsprojects.com/en/stable/testing/
[mongomock]: https://docs.mongoengine.org/guide/mongomock.html

## Features

- User authentication with JWT tokens (register/login)
- Role-based access control (Guest, Member, Trainer)
- Class management (create, view upcoming classes)
- Booking system with capacity management
- Trainer-specific features (view class rosters)
- Email Reminder Feature

# Running Locally

## 1. Start MongoDB

Before launching the server, ensure that MongoDB is running:

- **macOS:** `brew services restart mongodb-community`
- **Linux:** `sudo systemctl restart mongod`

---

## 2. Configure the `.env` File

Create a `.env` file in the root directory of your project. Here is a sample .env file (THIS IS THE BARE MINIMUM):

    # database configs
    MONGO_URI="mongodb://localhost:27017"
    DB_NAME="fitness_class_dev"
    MOCK_DB="false"

    # server config
    DEBUG="true"
    JWT_SECRET_KEY="9f8c1e5a6b4d3c2e1a9b8f7d6c5e4a3b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4"
    SES_SENDER_EMAIL="NYUAD.GYM@gmail.com"

> Note: This assumes you have an active, production-grade AWS account with Amazon SES email functionality enabled. For more information, check out this: [Link](https://aws.amazon.com/ses/).

---

## 3. Set Up Virtual Environment and Install Dependencies

Run:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt


## 4. Running the server

1. Run `make run_local_server` to run the server. This will also run the tests first.
2. Go to [http://127.0.0.1:8000](http://127.0.0.1:8000) to see it running!

You can use `ctrl-c` to stop the server.

> Note: Alternatively, you can run the following command: `FLASK_APP=app flask run --debug --host=0.0.0.0 --port 8000`

## 5. (Optional) Testing the API server

Run `make tests` to execute the test suite and see the coverage report
in your terminal. You can also see a visual report by viewing
[/htmlcov/index.html](/htmlcov/index.html) in your browser.


## Project Structure

- `/app/apis/` - REST API endpoints (auth, classes, bookings)
- `/app/db/` - Database models and operations
- `/docs/` - Project documentation
- `/reports/` - Requirements and specifications
- `/tests/` - test suits (targeting every functionality)

## Design Analysis Tools (Sprint 3A)

For the Sprint 3A design reflection analysis:

- **SonarQube** was used to identify code smells (for learning purposes).
- **PySequenceReverse** was used to generate sequence diagrams for the booking and reminder flows.
- Manual code review was also performed to identify design principle violations and validate findings.
- See [/reports/design_reflection.md](/reports/design_reflection.md) for the detailed design analysis, including UML diagrams and code smell documentation.

## Best Practices

See [/docs/BestPractices.md](/docs/BestPractices.md) for advice regarding branch naming and other useful tips.
