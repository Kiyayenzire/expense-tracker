import re
from django.core.exceptions import ValidationError

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit (0-9).")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")

    def get_help_text(self):
        return "Your password must contain at least 7 characters, one uppercase letter, one digit, and one special character."