"""Unit tests for models and business logic."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from accounts.models import User
from expenses.models import Category, SubCategory, Item, Currency, ExpenseEntry, CurrencyRate
from expenses.services.prediction_service import ExpensePredictor
from expenses.services.anomaly_service import detect_anomalies


@pytest.mark.unit
@pytest.mark.django_db
class TestUserModel:
    """Tests for User model."""
    
    def test_create_user(self, test_user):
        """Test creating a regular user."""
        assert test_user.username == 'testuser'
        assert test_user.email == 'test@example.com'
        assert test_user.role == 'user'
        assert not test_user.is_admin()
    
    def test_user_is_admin_check(self, admin_user):
        """Test is_admin method."""
        assert admin_user.is_admin()
        assert admin_user.role == 'admin'
    
    def test_user_two_factor_enabled(self, db):
        """Test two factor authentication flag."""
        user = User.objects.create_user(
            username='2fa_user',
            email='2fa@example.com',
            password='pass123',
            two_factor_enabled=True
        )
        assert user.two_factor_enabled is True

    def test_user_profile_picture_field_exists(self, db):
        """Profile pictures should be supported on the user model."""
        user = User.objects.create_user(
            username='avatar_user',
            email='avatar@example.com',
            password='pass123'
        )
        assert hasattr(user, 'profile_picture')
        assert not user.profile_picture.name

    def test_profile_picture_url_uses_absolute_backend_url(self, db):
        """Profile image URLs should point to the backend media host for the browser to render them."""
        user = User.objects.create_user(
            username='avatar_user_absolute',
            email='avatar-absolute@example.com',
            password='pass123'
        )
        user.profile_picture = 'profile_pictures/avatar_user_absolute/avatar.png'
        user.save(update_fields=['profile_picture'])

        serializer = __import__('accounts.serializers', fromlist=['UserProfileSerializer']).UserProfileSerializer(
            user,
            context={'request': type('RequestStub', (), {'build_absolute_uri': lambda self, url: f'http://localhost:8000{url}'})()}
        )

        payload = serializer.data
        assert payload['profile_picture_url'] == 'http://localhost:8000/media/profile_pictures/avatar_user_absolute/avatar.png'

    def test_user_can_request_account_deletion(self, test_user):
        """A verified deletion request should create a pending deletion state."""
        test_user.request_account_deletion('testpass123')

        assert test_user.account_deletion_requested_at is not None
        assert test_user.is_account_deletion_pending is True

    def test_login_cancels_pending_account_deletion(self, test_user):
        """Logging in should clear an outstanding deletion request."""
        test_user.account_deletion_requested_at = timezone.now() - timedelta(days=2)
        test_user.save(update_fields=['account_deletion_requested_at'])

        test_user.cancel_account_deletion()

        assert test_user.account_deletion_requested_at is None
        assert test_user.is_account_deletion_pending is False

    def test_expired_account_deletions_are_removed(self, test_user):
        """Users who did not cancel in time should be deleted after 31 days."""
        test_user.account_deletion_requested_at = timezone.now() - timedelta(days=32)
        test_user.save(update_fields=['account_deletion_requested_at'])

        deleted_count = User.objects.delete_expired_account_deletions()

        assert deleted_count == 1


@pytest.mark.unit
@pytest.mark.django_db
class TestCategoryModel:
    """Tests for Category model."""
    
    def test_create_category(self, category):
        """Test creating a category."""
        assert category.name == 'Groceries'
        assert category.color == '#10B981'
        assert category.is_active is True
    
    def test_category_string_representation(self, category):
        """Test category string representation."""
        assert str(category) == 'Groceries'
    
    def test_category_unique_name(self, db):
        """Test that category names must be unique."""
        Category.objects.create(name='Groceries')
        with pytest.raises(Exception):
            Category.objects.create(name='Groceries')
    
    def test_inactive_category(self, db):
        """Test creating an inactive category."""
        cat = Category.objects.create(
            name='Inactive',
            is_active=False
        )
        assert cat.is_active is False


@pytest.mark.unit
@pytest.mark.django_db
class TestSubCategoryModel:
    """Tests for SubCategory model."""
    
    def test_create_subcategory(self, subcategory):
        """Test creating a subcategory."""
        assert subcategory.name == 'Vegetables'
        assert subcategory.category.name == 'Groceries'
    
    def test_subcategory_string_representation(self, subcategory):
        """Test subcategory string representation."""
        assert str(subcategory) == 'Groceries - Vegetables'
    
    def test_subcategory_unique_together(self, category, db):
        """Test unique together constraint on name and category."""
        SubCategory.objects.create(name='Vegetables', category=category)
        with pytest.raises(Exception):
            SubCategory.objects.create(name='Vegetables', category=category)


@pytest.mark.unit
@pytest.mark.django_db
class TestItemModel:
    """Tests for Item model."""
    
    def test_create_item(self, item):
        """Test creating an item."""
        assert item.description == 'Tomatoes'
        assert item.category.name == 'Groceries'
    
    def test_item_string_representation(self, item):
        """Test item string representation."""
        assert str(item) == 'Tomatoes'


@pytest.mark.unit
@pytest.mark.django_db
class TestCurrencyModel:
    """Tests for Currency model."""
    
    def test_create_currency(self, currency):
        """Test creating a currency."""
        assert currency.code == 'EUR'
        assert currency.name == 'Euro'
        assert currency.symbol == '€'
        assert currency.is_active is True
    
    def test_currency_string_representation(self, currency):
        """Test currency string representation."""
        assert str(currency) == 'EUR'
    
    def test_currency_unique_code(self, db):
        """Test that currency codes must be unique."""
        Currency.objects.create(code='EUR', name='Euro')
        with pytest.raises(Exception):
            Currency.objects.create(code='EUR', name='European Union')


@pytest.mark.unit
@pytest.mark.django_db
class TestCurrencyRateModel:
    """Tests for CurrencyRate model."""
    
    def test_create_currency_rate(self, currency_rate):
        """Test creating a currency rate."""
        assert currency_rate.rate == Decimal('1.10')
        assert currency_rate.base_currency.code == 'EUR'
        assert currency_rate.target_currency.code == 'USD'
    
    def test_currency_rate_string_representation(self, currency_rate):
        """Test currency rate string representation."""
        assert str(currency_rate) == f'EUR->USD @ {date.today()}'
    
    def test_currency_rate_unique_together(self, currency, usd_currency, db):
        """Test unique together constraint on currencies and date."""
        CurrencyRate.objects.create(
            base_currency=currency,
            target_currency=usd_currency,
            rate=Decimal('1.10'),
            effective_date=date.today()
        )
        with pytest.raises(Exception):
            CurrencyRate.objects.create(
                base_currency=currency,
                target_currency=usd_currency,
                rate=Decimal('1.15'),
                effective_date=date.today()
            )


@pytest.mark.unit
@pytest.mark.django_db
class TestExpenseEntryModel:
    """Tests for ExpenseEntry model."""
    
    def test_create_expense_entry(self, expense_entry):
        """Test creating an expense entry."""
        assert expense_entry.user.username == 'testuser'
        assert expense_entry.category.name == 'Groceries'
        assert expense_entry.amount == Decimal('25.50')
        assert expense_entry.quantity == Decimal('2.5')
    
    def test_expense_entry_string_representation(self, expense_entry):
        """Test expense entry string representation."""
        expected = f'{date.today()} Groceries 25.50 EUR'
        assert str(expense_entry) == expected
    
    def test_expense_entry_ordering(self, multiple_expenses):
        """Test that expenses are ordered by date."""
        entries = ExpenseEntry.objects.all()
        dates = [e.date for e in entries]
        assert dates == sorted(dates, reverse=True)
    
    def test_expense_entry_default_quantity(self, db, test_user, category, item, currency):
        """Test default quantity is 1."""
        expense = ExpenseEntry.objects.create(
            user=test_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('10'),
            currency=currency
        )
        assert expense.quantity == Decimal('1')


@pytest.mark.unit
@pytest.mark.django_db
class TestExpensePredictionService:
    """Tests for ExpensePredictor service."""
    
    def test_predict_with_no_data(self, test_user):
        """Test prediction returns empty dict when user has no expenses."""
        predictor = ExpensePredictor(test_user)
        predictions = predictor.predict_next_month()
        assert predictions == {}
    
    def test_predict_with_single_category(self, multiple_expenses, test_user):
        """Test prediction with single category."""
        predictor = ExpensePredictor(test_user)
        predictions = predictor.predict_next_month()
        assert len(predictions) > 0
    
    def test_predict_returns_positive_values(self, multiple_expenses, test_user):
        """Test that predictions are positive values."""
        predictor = ExpensePredictor(test_user)
        predictions = predictor.predict_next_month()
        for category, amount in predictions.items():
            assert amount >= 0


@pytest.mark.unit
@pytest.mark.django_db
class TestAnomalyDetectionService:
    """Tests for anomaly detection service."""
    
    def test_detect_anomalies_no_data(self, test_user):
        """Test anomaly detection with no expenses."""
        anomalies = detect_anomalies(test_user)
        assert anomalies == []
    
    def test_detect_anomalies_with_outliers(self, db, test_user, category, item, currency):
        """Test anomaly detection identifies outliers."""
        # Create normal expenses
        for i in range(5):
            ExpenseEntry.objects.create(
                user=test_user,
                date=date.today() - timedelta(days=i),
                category=category,
                item=item,
                amount=Decimal('10'),
                currency=currency
            )
        
        # Create outlier expense
        ExpenseEntry.objects.create(
            user=test_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('1000'),
            currency=currency
        )
        
        anomalies = detect_anomalies(test_user)
        # Should detect the outlier
        assert len(anomalies) > 0
