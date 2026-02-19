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

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user (member or trainer)
- `POST /auth/login` - Login and receive JWT token

### Classes
- `GET /classes` - View all upcoming classes (public)
- `POST /classes` - Create a new class (trainers only)
- `GET /classes/<class_id>/members` - View members who booked a class (trainer of that class only)

### Bookings
- `POST /bookings` - Book a class (members only)

## Running Locally

This assumes you are already running MongoDB (e.g., through
`brew services restart mongodb-community` on MacOS or
`sudo systemctl restart mongod` on Linux.
Find the equivalent for your OS)

### Setting up the environment

1. Create a `.env` file in the root of your project and include the following variables:

- `MONGO_URI` – The connection string for your MongoDB database.
- `DB_NAME` – The name of the database your application will use.
- `MOCK_DB` – Set to `true` to use a mock database (for testing), or `false` to use the real database.
- `DEBUG` – Enable debug mode by setting this to `true` (optional, useful for development).
- `JWT_SECRET_KEY` – A secret key used to sign and verify JWT authentication tokens.

2. Run `make dev_env` to create a virtual environment and install dependencies

### Running the server

1. Run `make run_local_server` to run the server. This will also run the tests first.
2. Go to [http://127.0.0.1:8000](http://127.0.0.1:8000) to see it running!

You can use `ctrl-c` to stop the server.

### Testing the API server

Run `make tests` to execute the test suite and see the coverage report
in your terminal. You can also see a visual report by viewing
[/htmlcov/index.html](/htmlcov/index.html) in your browser.

### Manually activating and deactivating the virtual environment

Manually activating and deactivating the virtual environment is useful for
debugging issues and running specific scripts with flexibility (e.g., you can
run `FLASK_APP=app flask run --debug --host=0.0.0.0 --port 8000`
inside the virtual environment to directly start
the server without running tests first).

To activate the virtual environment manually:

```sh
source .venv/bin/activate
```

Alternatively, you can use:

```sh
. .venv/bin/activate
```

To deactivate the virtual environment:

```sh
deactivate
```

## Project Structure

- `/app/apis/` - REST API endpoints (auth, classes, bookings)
- `/app/db/` - Database models and operations
- `/docs/` - Project documentation
- `/reports/` - Requirements and specifications

## Best Practices

See [/docs/BestPractices.md](/docs/BestPractices.md) for advice regarding branch naming and other useful tips.
