import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from autenticacion.models import CustomUser
from .forms import SchoolConfigurationForm


class UserManagementTests(TestCase):
    def test_delete_user_desactiva_en_lugar_de_borrar(self):
        admin = CustomUser.objects.create_user(email='admin-school@test.com', password='ClaveSegura123', is_admin=True)
        user = CustomUser.objects.create_user(email='target-school@test.com', password='ClaveSegura123')

        self.client.force_login(admin)
        response = self.client.post(reverse('delete_user', args=[user.pk]))
        user.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_locked)
        self.assertTrue(CustomUser.objects.filter(pk=user.pk).exists())

    def test_restaurar_usuario_desactivado(self):
        admin = CustomUser.objects.create_user(email='admin-restore@test.com', password='ClaveSegura123', is_admin=True)
        user = CustomUser.objects.create_user(email='target-restore@test.com', password='ClaveSegura123', is_active=False, is_locked=True)

        self.client.force_login(admin)
        response = self.client.post(reverse('restore_user', args=[user.pk]))
        user.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_locked)


class SystemOperationsTests(TestCase):
    def test_configuracion_rechaza_ano_escolar_invalido(self):
        form = SchoolConfigurationForm(data={
            'institution_name': 'Colegio',
            'active_academic_year': '2025-2027',
            'director_name': '',
            'director_document': '',
            'rif': '',
            'dea_code': '',
            'phone': '',
            'email': '',
            'address': '',
            'report_footer': '',
            'payment_reminder_days': '3',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('active_academic_year', form.errors)

    def test_backup_system_crea_zip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db = Path(temp_dir) / 'db.sqlite3'
            temp_db.write_text('sqlite backup test', encoding='utf-8')
            databases = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(temp_db)}}
            with override_settings(DATABASES=databases, MEDIA_ROOT=Path(temp_dir) / 'media'):
                call_command('backup_system', output_dir=temp_dir, verbosity=0)
                backups = list(Path(temp_dir).glob('*.zip'))

        self.assertEqual(len(backups), 1)
