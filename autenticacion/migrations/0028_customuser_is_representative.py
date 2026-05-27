from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacion', '0027_otpverificacion_intentos_enviado_en'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_representative',
            field=models.BooleanField(default=False),
        ),
    ]
