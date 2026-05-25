from django.test import TestCase

from .models import CustomUser


class CustomUserManagerTests(TestCase):
    def test_requiere_correo_para_crear_usuario(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', password='ClaveSegura123')
