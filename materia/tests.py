from django.test import TestCase

from .forms import SubjectForm
from .models import Subject


class SubjectFormTests(TestCase):
    def test_rechaza_codigo_duplicado(self):
        Subject.objects.create(code='MAT', name='Matemática')
        form = SubjectForm(data={'code': 'MAT', 'name': 'Matemática II'})
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)
