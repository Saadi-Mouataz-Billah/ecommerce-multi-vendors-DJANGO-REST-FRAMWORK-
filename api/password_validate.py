import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password):
        validation_errors = []
        if len(password) < 8:
            validation_errors.append("Password must be at least 8 characters long.")
            raise ValidationError(
                _("Password must be at least 8 characters long."),
                code='password_too_short',
            )

        if not re.search(r"[A-Z]", password):
            validation_errors.append("Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character.")
            raise ValidationError(
                _("Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character."),
                code='password_no_upper',
            )
        if not re.search(r"[a-z]", password):
            validation_errors.append("Password must contain at least one lowercase letter.")
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        if not re.search(r"\d", password):
            validation_errors.append("Password must contain at least one number.")
            raise ValidationError(
                _("Password must contain at least one number."),
                code='password_no_digit',
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            validation_errors.append("Password must contain at least one special character.")
            raise ValidationError(
                _("Password must contain at least one special character."),
                code='password_no_special',
            )
        #return validation_errors

    def get_help_text(self):
        return _(
            "Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character."
        )
