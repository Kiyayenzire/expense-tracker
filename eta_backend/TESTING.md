# ETA Application - Testing Guide

## Overview

The ETA application includes a comprehensive pytest test suite with **50+ real test cases** organized into three categories:

* Unit tests
* Integration tests
* End-to-end tests

The tests cover the major application features, including:

* Expense tracking
* Multi-currency support
* Expense predictions
* Anomaly detection
* API permissions
* Reporting
* Data ownership

## Quick Start

### 1. Install Dependencies

```bash
cd backend

pip install -r requirements/test.txt
```

### 2. Run All Tests

```bash
pytest
```

### 3. Run Specific Test Categories

#### Unit tests

Fast, isolated tests:

```bash
pytest -m unit
```

#### Integration tests

Tests involving multiple application components and the database:

```bash
pytest -m integration
```

#### End-to-end tests

Tests complete application workflows:

```bash
pytest -m e2e
```

#### Run all tests except slow tests

```bash
pytest -m "not slow"
```

### 4. Run with Coverage Report

#### Terminal report

```bash
pytest --cov=accounts --cov=expenses --cov-report=term-missing
```

#### HTML report

```bash
pytest --cov=accounts --cov=expenses --cov-report=html
```

Then open:

```text
htmlcov/index.html
```

## Test Structure

### Unit Tests (`tests/unit/`)

**Purpose:** Fast, isolated tests for individual components.

**Speed:** Less than 1 second for the entire suite.

**Dependencies:** No database by default.

#### Coverage

Unit tests cover:

* **User Model:** Authentication, roles, and permissions
* **Category Model:** Creation, validation, and uniqueness constraints
* **SubCategory Model:** Hierarchies and constraints
* **Item Model:** Item management
* **Currency Model:** Multi-currency support
* **CurrencyRate Model:** Exchange rates
* **ExpenseEntry Model:** Expense creation and ordering
* **Services:** Prediction and anomaly detection algorithms

#### Example

```bash
pytest tests/unit/ -v
```

Run a specific test:

```bash
pytest tests/unit/test_example.py::TestUserModel::test_create_user -v
```

## Integration Tests (`tests/integration/`)

**Purpose:** Test interactions between application components and API endpoints.

**Speed:** Approximately 5-10 seconds.

**Dependencies:** Database and Django models.

#### Coverage

Integration tests cover:

* **Category API:** List, create, and filter operations
* **ExpenseEntry API:** CRUD operations and permissions
* **Summary Endpoints:** Daily, weekly, monthly, quarterly, and yearly totals
* **Chart Data:** Category analysis, most expensive, and least expensive expenses
* **Currency Conversion:** Exchange rate calculations
* **Export Reports:** Monthly and yearly exports with currency conversion
* **Predictions:** Expense prediction functionality
* **Insights:** Anomaly detection functionality

#### Example

```bash
pytest tests/integration/ -v
```

Run a specific test:

```bash
pytest tests/integration/test_example.py::TestExpenseEntryAPI::test_create_expense_entry -v
```

## End-to-End Tests (`tests/e2e/`)

**Purpose:** Test complete user workflows and combinations of application features.

**Speed:** Approximately 10-20 seconds.

**Dependencies:** Full application stack.

#### Coverage

End-to-end tests cover:

* **Expense Tracking Workflow:** Create expense → View summary → Get insights → Get predictions
* **Category Browsing:** Browse categories and items
* **Multi-Currency Workflow:** Track and convert expenses in different currencies
* **Reporting Workflow:** Generate monthly and yearly reports with analysis
* **Data Permissions:** Verify users can only access their own data and administrators can access appropriate data
* **Seasonal Analysis:** Track expenses across multiple months and periods

#### Example

```bash
pytest tests/e2e/ -v
```

Run a specific test:

```bash
pytest tests/e2e/test_example.py::TestUserExpenseWorkflow::test_complete_expense_tracking_workflow -v
```

## Test Fixtures

### User Fixtures

```text
test_user       # Regular user for testing
admin_user      # Admin user with staff privileges
```

### API Client Fixtures

```text
api_client            # Unauthenticated client
authenticated_client  # Client authenticated as test_user
admin_client          # Client authenticated as admin_user
```

### Model Fixtures

#### Single instances

```text
category       # Single category (Groceries)
subcategory    # Single subcategory (Vegetables)
item           # Single item (Tomatoes)
currency       # Single currency (EUR)
usd_currency   # USD currency
expense_entry  # Single expense entry
```

#### Multiple instances

```text
multiple_categories  # Four different categories
multiple_expenses    # Ten expenses spanning dates
```

### Advanced Fixtures

```text
category_rate    # Currency exchange rate EUR -> USD
mock_expense_data # Mock expense data dictionary
mock_user_data    # Mock user data dictionary
```

## Common Testing Patterns

### Testing Model Creation

```python
@pytest.mark.unit
@pytest.mark.django_db
class TestCategoryModel:

    def test_create_category(self, category):
        assert category.name == "Groceries"
        assert category.color == "#10B981"
```

### Testing API Endpoints

```python
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseEntryAPI:

    def test_create_expense_entry(
        self,
        authenticated_client,
        category,
        item,
        currency,
    ):
        data = {
            "date": "2024-01-15",
            "category": category.id,
            "item": item.id,
            "amount": "25.50",
            "currency": currency.id,
        }

        response = authenticated_client.post(
            "/api/expenses/",
            data,
        )

        assert response.status_code == 201
```

### Testing Permissions

```python
def test_user_cannot_see_other_user_expenses(
    self,
    authenticated_client,
    admin_client,
    ...
):
    # Create an expense as test_user.
    # Verify authenticated_client can see it.
    # Verify admin_client can see appropriate expenses.
    # Verify another user cannot see the expense.
```

### Testing Services

The prediction service is tested independently from the API.

For example:

```python
def test_predict_with_no_data(self, test_user):
    predictor = ExpensePredictor(test_user)

    predictions = predictor.predict_next_month()

    assert predictions == {
        "predictions": {},
        "high_volume_categories": [],
    }
```

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
- name: Run tests
  run: |
    pip install -r requirements/test.txt
    pytest --cov=accounts --cov=expenses --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

### Local CI Check

Run the full test suite with coverage and strict marker validation:

```bash
pytest \
    --cov=accounts \
    --cov=expenses \
    --cov-report=term-missing \
    --strict-markers
```

## Best Practices

### Do's

* Use meaningful test names such as `test_user_cannot_see_other_user_expenses()`.
* Use appropriate markers such as `@pytest.mark.unit` and `@pytest.mark.django_db`.
* Keep unit tests fast.
* Use fixtures to reduce duplication.
* Test edge cases and error conditions.
* Write regression tests when fixing bugs.
* Keep tests independent from one another.
* Run the test suite before pushing changes.

### Don'ts

* Don't create unnecessary database objects in tests.
* Don't hardcode values that should be parameterized.
* Don't test Django or DRF framework behavior itself.
* Don't make tests dependent on execution order.
* Don't ignore test failures.
* Don't remove a failing test simply to make CI pass.

## Debugging Tests

### Run a single test with verbose output

```bash
pytest tests/unit/test_example.py::TestUserModel::test_create_user -vv
```

### Show print statements

```bash
pytest -s
```

### Drop into the debugger on failure

```bash
pytest --pdb
```

### Show the slowest tests

```bash
pytest --durations=10
```

## Test Data

### Creating Test Expenses

Test expenses can be created using fixtures or directly in a test.

Example:

```python
from datetime import date
from decimal import Decimal

ExpenseEntry.objects.create(
    user=test_user,
    date=date.today(),
    category=category,
    item=item,
    quantity=Decimal("2.5"),
    amount=Decimal("25.50"),
    currency=currency,
    notes="Test expense",
)
```

### Creating Multiple Test Data

Use the `multiple_expenses` fixture when appropriate.

For custom scenarios, create the required records in the test:

```python
for i in range(10):
    ExpenseEntry.objects.create(
        user=test_user,
        date=date.today(),
        category=category,
        item=item,
        amount=Decimal("10.00"),
        currency=currency,
    )
```

## Common Issues and Solutions

### Issue: Tests fail due to timezone issues

**Solution:** Use `date.today()` for date-only comparisons when the application logic is based on dates. Use timezone-aware datetimes when testing datetime behavior.

### Issue: Foreign key constraint errors

**Solution:** Ensure all required related objects are created before creating the dependent model.

### Issue: Database not rolled back between tests

**Solution:** Use `@pytest.mark.django_db` for tests that require database access and let pytest-django manage the test database lifecycle.

### Issue: Fixture dependency errors

**Solution:** Ensure fixtures are declared as test function parameters and that the required fixture dependencies are available.

## Test Metrics

### Current Coverage

The current project targets the following coverage levels:

* **Models:** 95%+
* **Views:** 85%+
* **Services:** 80%+
* **Serializers:** 90%+

### Test Statistics

The current test suite includes:

* **Total Tests:** 50+
* **Unit Tests:** 30+
* **Integration Tests:** 12+
* **End-to-End Tests:** 8+
* **Fixtures:** 25+

These numbers should be updated when the test suite changes significantly.

## Next Steps

1. Add more tests for edge cases and business logic.
2. Integrate the test suite with GitHub Actions.
3. Work toward a 90%+ overall code coverage target.
4. Monitor test execution time as the project grows.
5. Add docstrings to complex test methods where they improve maintainability.

## Resources

* [Pytest Documentation](https://docs.pytest.org/)
* [pytest-django Documentation](https://pytest-django.readthedocs.io/)
* [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
* [Django REST Framework Testing Documentation](https://www.django-rest-framework.org/api-guide/testing/)

## Support

For issues or questions about the test suite:

1. Check existing tests for examples.
2. Review fixture definitions in `conftest.py`.
3. Check the Django and DRF documentation.
4. Run tests with the `-vv` flag for detailed output.
5. Run the failing test individually before changing application code.
