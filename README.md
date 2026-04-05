# Finance Data Processing API - Backend Evaluation

Welcome to my submission for the Finance Data Processing and Access Control Backend assignment. 

This README is designed specifically as a **Walkthrough Guide**. It outlines how the architecture maps directly to the assignment requirements, the design tradeoffs made, and a step-by-step guide to run and test the APIs locally.

---

## 1. Architecture & Design Philosophy

This project was built using **Django** and **Django REST Framework (DRF)**. To prove clean implementation and separation of concerns, I strictly utilized a **Service Layer Pattern**:
*   **API Views (`views.py`):** Strictly handle HTTP routing, parsing JSON into Data Transfer Objects (DTOs), and returning HTTP status codes. No business logic lives here.
*   **Service Layer (`services.py`):** Pure Python functions that execute database writes, math, and business logic. This makes the code highly testable (see Unit Tests).
*   **Policy Engine (`core/permissions.py`):** A custom Hierarchical RBAC engine that intercepts requests *before* they reach the service layer to guarantee Authorization boundaries.

**Tradeoffs & Assumptions:**
1.  **Database:** I architected the models for PostgreSQL (using strict `Decimal` types for money) but committed the project using **SQLite** as expressly permitted, ensuring you can test it locally without installing Docker or external database servers.
2.  **Pagination:** Standard numeric `PageNumberPagination` was chosen over Cursor Pagination for dashboard simplicity.
3.  **Soft Deletes:** I implemented a custom `ActiveRecordManager`. When ledgers are deleted, they are physically preserved in the database for financial auditing but logically hidden from all API queries.

---

## 2. Getting Started (Evaluator Setup)

You can run this entire backend in under a minute. Requires Python 3.10+.

**1. Activate Environment & Install Dependencies**
```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install django djangorestframework djangorestframework-simplejwt django-filter
```

**2. Initialize the Database & Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**3. Run the Automated Test Suite (Optional but Recommended)**
To prove the business rules (Negative amounts fail, Viewers are blocked, Soft deletes ghost records), I wrote explicit unit tests.
```bash
python manage.py test
```

---

## 🧪 3. Evaluator API Walkthrough

### Step 1: Create your Admin Account
Open a terminal and create the root Admin user overriding the CLI prompt.
```bash
python manage.py createsuperuser
```
*(Enter a username, email, and password. My custom `UserManager` natively intercepts this command and forces the `Role.ADMIN` enum into the database).*

### Step 2: Start the Web Server
```bash
python manage.py runserver
```

### Step 3: Get your Access Token (JWT)
The system is stateless. Send a POST request to retrieve your token (using Postman, Insomnia, or cURL).

`POST http://127.0.0.1:8000/api/v1/users/auth/token/`
```json
{
    "username": "<your_admin_username>",
    "password": "<your_admin_password>"
}
```
*Copy the `access` token. For all subsequent requests, pass it in the Headers:*
`Authorization: Bearer <your_access_token>`

---

### Step 4: Test Requirement 1 (User & Role Management)
You are an Admin. You can create users with specific access roles.

`POST http://127.0.0.1:8000/api/v1/users/`
```json
{
    "username": "evaluator_analyst",
    "password": "strongpassword123",
    "role": "ANALYST" 
}
```
*(Available roles: `VIEWER`, `ANALYST`, `ADMIN`).*

---

### Step 5: Test Requirement 2 (Financial Records CRUD)
Create a financial ledger entry. 

`POST http://127.0.0.1:8000/api/v1/records/`
```json
{
    "amount": "1500.50",
    "record_type": "INCOME",
    "category": "Consulting",
    "date": "2026-04-05",
    "notes": "Testing the API"
}
```
*Validation Proof: Try sending `"amount": "-500"`. The system will cleanly reject it with a standardized 400 Bad Request JSON response, executing Requirement 5 (Validation).*

**Test Paginating and Filtering:**
`GET http://127.0.0.1:8000/api/v1/records/?record_type=INCOME&start_date=2026-04-01`

---

### Step 6: Test Requirement 3 (Dashboard Aggregations)
Instead of forcing the frontend to fetch millions of rows to do math, this endpoint leverages raw Database `SUM()` and `Coalesce` logic to calculate metrics in milliseconds natively.

`GET http://127.0.0.1:8000/api/v1/dashboard/summary/`
```json
{
    "total_income": "1500.50",
    "total_expenses": "0.00",
    "net_balance": "1500.50"
}
```

---

### Step 7: Test Requirement 4 (Access Control Boundaries)
To prove the RBAC engine works:
1. Log in to `/api/v1/users/auth/token/` using the `evaluator_analyst` account you created in Step 4.
2. Attempt to `POST` a new Financial Record using that new Analyst token.
3. **Result:** The system will instantly reject the request with a `403 Forbidden` response, mathematically proving Analysts cannot mutate ledgers.

---

## ✅ Feature Checklist Completed
* [x] **User Management:** Create, Status toggling, Enum Roles.
* [x] **Financial Records:** DTO Validation, Income/Expense typing.
* [x] **Dashboard APIs:** Native SQL Aggregations (Total Income, Expenses, Balance).
* [x] **RBAC Logic:** Custom DRF hierarchical policy guards.
* [x] **Validation / Error Handling:** Try/Catch HTML traces disabled; all errors return strictly identical JSON interface schemas.
* [x] **Data Persistence:** SQLite implemented cleanly.

**Optional Features Built:**
* [x] JWT Authentication
* [x] Pagination (`django-filters`)
* [x] Query Parameter Searching
* [x] Soft Deletion
* [x] Test Driven Development (Unit/Integration Tests)
