from django.test import TestCase
from django.urls import reverse

from autenticacion.models import CustomUser
from escuela.models import Class, ClassTeacherAssignment
from profesor.models import Teacher
from .forms import SubjectForm
from .models import Subject


class SubjectFormTests(TestCase):
    def test_rechaza_codigo_duplicado(self):
        Subject.objects.create(code='MAT', name='Matematica')
        form = SubjectForm(data={'code': 'MAT', 'name': 'Matematica II'})
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)


class SubjectArchiveTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(email='admin-mat@test.com', password='ClaveSegura123', is_admin=True)
        self.subject = Subject.objects.create(code='ARC-MAT', name='Materia Archivo')

    def test_delete_subject_archiva_en_lugar_de_borrar(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('delete_subject', args=[self.subject.code]))
        self.subject.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.subject.is_archived)
        self.assertTrue(Subject.objects.filter(pk=self.subject.pk).exists())

    def test_restore_subject_reactiva_archivada(self):
        self.subject.is_archived = True
        self.subject.save(update_fields=['is_archived'])
        self.client.force_login(self.admin)

        response = self.client.post(reverse('restore_subject', args=[self.subject.code]))
        self.subject.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.subject.is_archived)

    def test_delete_assignment_desactiva_en_lugar_de_borrar(self):
        teacher = Teacher.objects.create(
            teacher_id='T-MAT', name='Profesor Materia', gender='Male', date_of_birth='1990-01-01',
            joining_date='2024-01-01', mobile_number='04140000000', qualification='Licenciado',
            experience='5', email='prof-mat@test.com', address='Direccion', city='Ciudad',
            state='Estado', country='Pais', zip_code='0000'
        )
        class_obj = Class.objects.create(class_id='MAT-1', section='A', academic_year='2025-01-01')
        assignment = ClassTeacherAssignment.objects.create(class_assigned=class_obj, teacher=teacher, subject=self.subject)

        self.client.force_login(self.admin)
        response = self.client.post(reverse('delete_assignment', args=[assignment.pk]))
        assignment.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(assignment.is_active)
        self.assertTrue(ClassTeacherAssignment.objects.filter(pk=assignment.pk).exists())
