from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexPasswordValidator:
    def validate(self, password, user=None):
        checks = [
            (any(char.isupper() for char in password), _('Debe incluir al menos una letra mayuscula.')),
            (any(char.islower() for char in password), _('Debe incluir al menos una letra minuscula.')),
            (any(char.isdigit() for char in password), _('Debe incluir al menos un numero.')),
            (any(not char.isalnum() for char in password), _('Debe incluir al menos un caracter especial.')),
        ]
        errors = [message for passed, message in checks if not passed]
        if errors:
            raise ValidationError(errors, code='password_no_complexity')

    def get_help_text(self):
        return _('Tu contraseña debe incluir mayusculas, minusculas, numeros y caracteres especiales.')
