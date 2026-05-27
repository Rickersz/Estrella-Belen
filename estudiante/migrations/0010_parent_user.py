from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('estudiante', '0009_enrollment_monto_inscripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='representante', to=settings.AUTH_USER_MODEL),
        ),
    ]
