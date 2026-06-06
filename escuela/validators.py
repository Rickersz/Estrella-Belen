import re

from django import forms


ACADEMIC_YEAR_RE = re.compile(r'^\d{4}-\d{4}$')
PHONE_RE = re.compile(r'^[0-9+\-\s()]{7,20}$')


def validate_academic_year(value):
    value = (value or '').strip()
    if not ACADEMIC_YEAR_RE.match(value):
        raise forms.ValidationError('Usa el formato 2025-2026.')
    start, end = value.split('-')
    if int(end) != int(start) + 1:
        raise forms.ValidationError('El ano escolar debe cubrir dos anos consecutivos.')
    return value


def validate_phone(value, label='telefono'):
    value = (value or '').strip()
    if value and not PHONE_RE.match(value):
        raise forms.ValidationError(f'El {label} solo puede contener numeros, espacios, +, - y parentesis.')
    return value
