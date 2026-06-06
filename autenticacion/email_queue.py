import logging
import queue
import threading

from django.conf import settings
from django.core.mail import send_mail


_email_queue = queue.Queue()
logger = logging.getLogger(__name__)


def _worker():
    while True:
        subject, message, recipient = _email_queue.get()
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
        except Exception:
            # Keep the web request fast, but leave a useful trail for admins.
            logger.exception('No se pudo enviar el correo a %s.', recipient)
        finally:
            _email_queue.task_done()


threading.Thread(target=_worker, daemon=True, name='auth-email-worker').start()


def enqueue_otp_email(recipient, codigo):
    _email_queue.put((
        'Codigo de verificacion - Estrella de Belen',
        (
            f'Tu codigo de verificacion es: {codigo}\n\n'
            f'Este codigo es valido por 10 minutos.\n'
            f'Si no solicitaste este codigo, ignora este mensaje.'
        ),
        recipient,
    ))


def enqueue_reset_email(recipient, reset_link):
    _email_queue.put((
        'Restablecer contrasena - Estrella de Belen',
        (
            'Recibimos una solicitud para restablecer tu contrasena.\n\n'
            f'Abre este enlace para crear una nueva contrasena:\n{reset_link}\n\n'
            'Este enlace es valido por 15 minutos. Si no solicitaste este cambio, ignora este mensaje.'
        ),
        recipient,
    ))


def enqueue_generic_email(subject, message, recipient):
    _email_queue.put((subject, message, recipient))
