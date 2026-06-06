from django.test import TestCase
from django.urls import reverse

from autenticacion.models import CustomUser
from escuela.models import Class, ClassTeacherAssignment, SchoolConfiguration
from materia.models import Subject
from profesor.models import Teacher
from .forms import EnrollmentForm, StudentForm
from .models import Student


class StudentFormTests(TestCase):
    def test_rechaza_cedula_escolar_duplicada(self):
        Student.objects.create(
            student_id='CE-001', first_name='Ana', last_name='Pérez', student_class='1',
            section='A', admission_number='ADM1', joining_date='2025-01-01',
            gender='Female', date_of_birth='2018-01-01'
        )
        form = StudentForm(data={
            'student_id': 'CE-001', 'first_name': 'Luis', 'last_name': 'Gómez',
            'student_class': '1', 'section': 'A', 'admission_number': 'ADM2',
            'joining_date': '2025-01-01', 'gender': 'Male', 'date_of_birth': '2018-01-01',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('student_id', form.errors)

    def test_rechaza_monto_negativo(self):
        form = EnrollmentForm(data={'monto_inscripcion': '-1'})
        self.assertFalse(form.is_valid())
        self.assertIn('monto_inscripcion', form.errors)


class StudentPermissionTests(TestCase):
    def test_usuario_estudiante_no_puede_inscribir(self):
        user = CustomUser.objects.create_user(email='estudiante@test.com', password='ClaveSegura123', is_student=True)
        self.client.force_login(user)
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 302)

    def test_panel_estudiante_responde(self):
        user = CustomUser.objects.create_user(email='estudiante-panel@test.com', password='ClaveSegura123', is_student=True)
        self.client.force_login(user)
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profesor_exporta_solo_sus_secciones(self):
        teacher_user = CustomUser.objects.create_user(email='teacher-student@test.com', password='ClaveSegura123', is_teacher=True)
        teacher = Teacher.objects.create(
            teacher_id='T-ST-1',
            name='Profesor CSV',
            gender='Male',
            date_of_birth='1990-01-01',
            joining_date='2025-01-01',
            mobile_number='0414000003',
            qualification='Docente',
            experience='5',
            email=teacher_user.email,
            address='Direccion',
            city='Ciudad',
            state='Estado',
            country='VE',
            zip_code='0000',
        )
        subject = Subject.objects.create(code='CSV-MAT', name='Matematica CSV')
        class_a = Class.objects.create(class_id='CSV-1', section='A', academic_year='2025-01-01')
        ClassTeacherAssignment.objects.create(class_assigned=class_a, teacher=teacher, subject=subject)
        Student.objects.create(
            student_id='CSV-001', first_name='Ana', last_name='SeccionA', student_class='1',
            section='A', admission_number='CSV1', joining_date='2025-01-01',
            gender='Female', date_of_birth='2018-01-01',
        )
        Student.objects.create(
            student_id='CSV-002', first_name='Luis', last_name='SeccionB', student_class='1',
            section='B', admission_number='CSV2', joining_date='2025-01-01',
            gender='Male', date_of_birth='2018-01-01',
        )

        self.client.force_login(teacher_user)
        response = self.client.get(reverse('download_students_csv'))
        body = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertIn('CSV-001', body)
        self.assertNotIn('CSV-002', body)

    def test_admin_archiva_estudiante_en_lugar_de_borrarlo(self):
        admin = CustomUser.objects.create_user(email='admin-student@test.com', password='ClaveSegura123', is_admin=True)
        student = Student.objects.create(
            student_id='ARC-001', first_name='Archivado', last_name='Seguro', student_class='1',
            section='A', admission_number='ARC1', joining_date='2025-01-01',
            gender='Male', date_of_birth='2018-01-01',
        )

        self.client.force_login(admin)
        response = self.client.post(reverse('delete_student', args=[student.slug]))
        student.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(student.is_archived)
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())

    def test_admin_restaura_estudiante_archivado(self):
        admin = CustomUser.objects.create_user(email='admin-restore-student@test.com', password='ClaveSegura123', is_admin=True)
        student = Student.objects.create(
            student_id='RST-001', first_name='Restaurar', last_name='Seguro', student_class='1',
            section='A', admission_number='RST1', joining_date='2025-01-01',
            gender='Male', date_of_birth='2018-01-01', is_archived=True,
        )

        self.client.force_login(admin)
        response = self.client.post(reverse('restore_student', args=[student.slug]))
        student.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(student.is_archived)

    def test_constancia_imprimible_usa_configuracion_institucional(self):
        admin = CustomUser.objects.create_user(email='admin-constancia@test.com', password='ClaveSegura123', is_admin=True)
        config = SchoolConfiguration.get_solo()
        config.institution_name = 'Colegio Desde Config'
        config.director_name = 'Directora Desde Config'
        config.rif = 'J-CONFIG'
        config.dea_code = 'DEA-CONFIG'
        config.report_footer = 'Pie desde config'
        config.save()
        student = Student.objects.create(
            student_id='CFG-001', first_name='Config', last_name='Constancia', student_class='1',
            section='A', admission_number='CFG1', joining_date='2025-01-01',
            gender='Female', date_of_birth='2018-01-01',
        )

        self.client.force_login(admin)
        response = self.client.get(reverse('constancia_inscripcion', args=[student.slug]))
        body = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Colegio Desde Config', body)
        self.assertIn('Directora Desde Config', body)
        self.assertIn('J-CONFIG', body)
        self.assertIn('DEA-CONFIG', body)
        self.assertIn('Pie desde config', body)
