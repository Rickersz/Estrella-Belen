from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticacion.models import CustomUser
from estudiante.models import Parent, Student
from .models import Payment


class PaymentModelTests(TestCase):
    def setUp(self):
        self.parent = Parent.objects.create(
            father_name='Padre', father_mobile='04140000000',
            mother_name='Madre', mother_mobile='04140000001',
        )
        self.student = Student.objects.create(
            student_id='CE-100', first_name='Ana', last_name='Perez', student_class='1',
            section='A', admission_number='A1', joining_date='2025-01-01',
            gender='Female', date_of_birth='2018-01-01', parent=self.parent,
        )

    def test_estado_pagado_cuando_no_hay_saldo(self):
        payment = Payment.objects.create(
            student=self.student,
            due_date=timezone.localdate(),
            amount_due=Decimal('50.00'),
            amount_paid=Decimal('50.00'),
        )
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(payment.balance, Decimal('0.00'))

    def test_estado_vencido_cuando_hay_saldo_y_fecha_pasada(self):
        payment = Payment.objects.create(
            student=self.student,
            due_date=timezone.localdate() - timezone.timedelta(days=1),
            amount_due=Decimal('50.00'),
            amount_paid=Decimal('0.00'),
        )
        self.assertEqual(payment.status, Payment.STATUS_OVERDUE)
        self.assertEqual(payment.balance, Decimal('50.00'))


class PaymentPermissionTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(email='admin@test.com', password='ClaveSegura123', is_admin=True)
        self.rep_user = CustomUser.objects.create_user(email='rep@test.com', password='ClaveSegura123', is_representative=True)
        self.teacher = CustomUser.objects.create_user(email='teacher@test.com', password='ClaveSegura123', is_teacher=True)
        self.parent = Parent.objects.create(
            user=self.rep_user,
            father_name='Padre', father_mobile='04140000000',
            mother_name='Madre', mother_mobile='04140000001',
        )
        self.student = Student.objects.create(
            student_id='CE-200', first_name='Luis', last_name='Gomez', student_class='1',
            section='A', admission_number='A2', joining_date='2025-01-01',
            gender='Male', date_of_birth='2018-01-01', parent=self.parent,
        )
        self.payment = Payment.objects.create(
            student=self.student,
            due_date=timezone.localdate(),
            amount_due=Decimal('40.00'),
        )

    def test_admin_puede_ver_panel_pagos(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('payment_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_representante_puede_ver_sus_pagos(self):
        self.client.force_login(self.rep_user)
        response = self.client.get(reverse('payment_detail', args=[self.payment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_profesor_no_puede_ver_pagos(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('payment_dashboard'))
        self.assertEqual(response.status_code, 302)
