# Library Management System

A desktop-oriented library management application: catalogue books and categories,
register users, borrow and return books, and track borrowing transactions against
an Oracle database.

## Architecture

An MVC-structured Python application on top of Oracle via PL/SQL.

```text
main.py            Entry point
config.py          Configuration and database settings
db_connection.py   Oracle connection handling
database.sql       Schema and seed data
models/            Data access layer (book, category, user, borrow transaction)
controllers/       Request handling and business rules
views/             Presentation layer
resources/         Icons and styles
```

## Requirements

- Python 3
- An Oracle Database instance
- An Oracle client/driver compatible with your Python version

## Setup

1. Create the database schema:

   ```sql
   @database.sql
   ```

2. Update `config.py` with your connection details.
3. Run the application:

   ```bash
   python main.py
   ```

## Smoke tests

Small scripts are included to check connectivity and individual flows:

```bash
python test_connect.py
python test_return_page.py
```

## Features

- Book catalogue with categories
- Borrowing and return workflow
- Borrow transaction tracking
- User management
- Desktop UI with bundled icons and styles
