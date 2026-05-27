from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('estudiante', '0010_parent_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Mensualidad', max_length=120)),
                ('academic_year', models.CharField(default='2025-2026', max_length=9)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('due_day', models.PositiveSmallIntegerField(default=5)),
                ('allowed_days', models.PositiveSmallIntegerField(default=5)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-is_active', 'academic_year', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concept', models.CharField(default='Mensualidad', max_length=150)),
                ('academic_year', models.CharField(default='2025-2026', max_length=9)),
                ('due_date', models.DateField()),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=12)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('pagado', 'Pagado'), ('pendiente', 'Pendiente'), ('parcial', 'Parcial'), ('vencido', 'Vencido')], default='pendiente', max_length=20)),
                ('reference', models.CharField(blank=True, max_length=80)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments_created', to=settings.AUTH_USER_MODEL)),
                ('representative', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='estudiante.parent')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='estudiante.student')),
            ],
            options={
                'ordering': ['-due_date', 'student__last_name'],
            },
        ),
        migrations.CreateModel(
            name='PaymentReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='pagos.payment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', 'due_date'], name='pagos_payme_status_8ae200_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['student', 'academic_year'], name='pagos_payme_student_a1011a_idx'),
        ),
    ]
