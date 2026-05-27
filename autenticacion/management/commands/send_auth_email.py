from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Send authentication emails outside the web request.'

    def add_arguments(self, parser):
        parser.add_argument('kind', choices=['otp', 'reset'])
        parser.add_argument('recipient')
        parser.add_argument('payload')

    def handle(self, *args, **options):
        kind = options['kind']
        recipient = options['recipient']
        payload = options['payload']

        if kind == 'otp':
            subject = 'Codigo de verificacion - Estrella de Belen'
            message = (
                f'Tu codigo de verificacion es: {payload}\n\n'
                f'Este codigo es valido por 10 minutos.\n'
                f'Si no solicitaste este codigo, ignora este mensaje.'
            )
        elif kind == 'reset':
            subject = 'Restablecer contraseña - Estrella de Belen'
            message = (
                'Recibimos una solicitud para restablecer tu contraseña.\n\n'
                f'Abre este enlace para crear una nueva contraseña:\n{payload}\n\n'
                'Este enlace es valido por 15 minutos. Si no solicitaste este cambio, ignora este mensaje.'
            )
        else:
            raise CommandError('Tipo de correo no soportado.')

        sent = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        self.stdout.write(f'enviados={sent}')
