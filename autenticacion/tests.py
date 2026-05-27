from django.test import TestCase
from django.urls import reverse

from .models import AccessRequest, CustomUser, OTPVerificacion


class CustomUserManagerTests(TestCase):
    def test_requiere_correo_para_crear_usuario(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', password='ClaveSegura123')


class AuthenticationFlowTests(TestCase):
    def test_registro_publico_crea_solicitud_no_usuario(self):
        response = self.client.post(reverse('registrarse'), {
            'full_name': 'Ana Perez',
            'email': 'ana@test.com',
            'phone': '04141234567',
            'document_id': 'V123',
            'student_name': 'Luis Perez',
            'student_grade': '3A',
            'relationship': 'Madre',
        })

        self.assertRedirects(response, reverse('iniciar_sesion'))
        self.assertFalse(CustomUser.objects.filter(email='ana@test.com').exists())
        request = AccessRequest.objects.get(email='ana@test.com')
        self.assertEqual(request.status, AccessRequest.STATUS_PENDING)
        self.assertEqual(request.student_name, 'Luis Perez')

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
