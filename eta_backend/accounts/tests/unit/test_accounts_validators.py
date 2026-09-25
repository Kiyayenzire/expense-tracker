import pytest
from django.core.exceptions import ValidationError

from accounts.validators import CustomPasswordValidator


@pytest.mark.unit
class TestAccountsPasswordValidator:
    def test_password_requires_uppercase_letter(self):
        validator = CustomPasswordValidator()
        with pytest.raises(ValidationError):
            validator.validate('lowercase123!')

    def test_password_requires_digit(self):
        validator = CustomPasswordValidator()
        with pytest.raises(ValidationError):
            validator.validate('StrongPassword!')

    def test_password_requires_special_character(self):
        validator = CustomPasswordValidator()
        with pytest.raises(ValidationError):
            validator.validate('StrongPassword1')

    def test_password_valid(self):
        validator = CustomPasswordValidator()
        validator.validate('StrongPassword1!')
