import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class NumberValidator:
    def validate(self, password, user=None):
        if re.search(r'[0-9]', password) is None:
            raise ValidationError(
                _("Password must include a number."),
                code="password_must_include_number",
            )

    def get_help_text(self):
        return _("Your password must include at least one number.")


class LetterValidator:
    def validate(self, password, user=None):
        if re.search(r'[a-zA-Z]', password) is None:
            raise ValidationError(
                _("Password must include a letter."),
                code="password_must_include_letter",
            )

    def get_help_text(self):
        return _("Your password must include at least one letter.")


class SpecialCharValidator:
    def validate(self, password, user=None):
        if re.search(r'[@_!#$%^&*()<>?/\|}{~:]', password) is None:
            raise ValidationError(
                _("Password must include a special character."),
                code="password_must_include_special_char",
            )

    def get_help_text(self):
        return _("Your password must include at least one special character: @_!#$%^&*()<>?/\\|}{~:")