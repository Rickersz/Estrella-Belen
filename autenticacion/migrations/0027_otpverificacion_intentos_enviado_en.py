from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autenticacion', '0026_otpverificacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='otpverificacion',
            name='intentos',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='otpverificacion',
            name='enviado_en',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='otpverificacion',
            name='enviado_en',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
