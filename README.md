# Credit Approval System

A Django-based backend system for credit approval using historical loan data and customer information.


## API Endpoints

- `POST /register/` - Register a new customer
- `POST /check-eligibility/` - Check loan eligibility
- `POST /create-loan/` - Create a new loan
- `GET /view-loan/<loan_id>/` - View loan details
- `GET /view-loans/<customer_id>/` - View all customer loans

## Setup and Installation

### Using Docker

1. Clone the repository
2. Make sure Docker and Docker Compose are installed
3. Make sure you are into root directory to run teh command.
4. Run the application

### Build using Docker
```bash
docker-compose build --no-cache
```

### Compose up using Docker
```bash
docker-compose up
```

This will start:
- PostgreSQL database on port 5432
- Redis for Celery on port 6379
- Django application on port 8000
- Celery worker for background tasks

## Data Files

The system expects two Excel files in the root directory:
- `customer_data.xlsx` - Customer information
- `loan_data.xlsx` - Historical loan data

## Credit Scoring Algorithm

Credit scores (0-100) are calculated based on:
1. Past loans paid on time (35%)
2. Number of loans taken (15%) 
3. Loan activity in current year (15%)
4. Loan approved volume vs limit (35%)

## Loan Approval Criteria

- Credit score > 50: Approve loan
- Credit score 30-50: Approve with interest rate > 12%
- Credit score 10-30: Approve with interest rate > 16%
- Credit score < 10: Reject loan
- EMIs > 50% of salary: Reject loan

## Admin Panel

Access the Django admin panel at:
```bash
http://localhost:8000/admin/
```
- Username: admin
- Password: admin123

## Testing

The application includes comprehensive error handling and logging for all API endpoints.

### Run the Test Suite:
```bash
docker-compose exec web python run_tests.py
```
