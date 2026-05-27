from django.test import TestCase
from django.urls import reverse

from .models import CustomUser, OTPVerificacion


class CustomUserManagerTests(TestCase):
    def test_requiere_correo_para_crear_usuario(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', password='ClaveSegura123')


class AuthenticationFlowTests(TestCase):
    def test_registro_queda_pendiente_de_aprobacion(self):
        response = self.client.post(reverse('registrarse'), {
            'first_name': 'Ana',
            'last_name': 'Perez',
            'email': 'ana@test.com',
            'password': 'ClaveSegura123',
            'confirm_password': 'ClaveSegura123',
        })

        user = CustomUser.objects.get(email='ana@test.com')
        self.assertRedirects(response, reverse('iniciar_sesion'))
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_authorized)
        self.assertTrue(user.is_student)

    def test_recuperacion_no_revela_si_el_correo_existe(self):
        response = self.client.post(reverse('recuperar_contrasena'), {'email': 'nadie@test.com'})

        self.assertRedirects(response, reverse('recuperar_contrasena'))
        messages = [str(message) for message in response.wsgi_request._messages]
        self.assertTrue(messages)
        self.assertNotIn('No existe', messages[0])

    def test_otp_bloquea_usuario_tras_intentos_invalidos(self):
        user = CustomUser.objects.create_user(email='user@test.com', password='ClaveSegura123', is_active=True)
        otp = OTPVerificacion.objects.create(user=user, codigo='123456')
        session = self.client.session
        session['otp_user_id'] = user.pk
        session.save()

        for _ in range(5):
            self.client.post(reverse('verificar_otp'), {'codigo': '000000'})

        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(user.is_locked)
        self.assertEqual(otp.intentos, 5)
