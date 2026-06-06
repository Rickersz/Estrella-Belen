from django.core.management.base import BaseCommand

from pagos.utils import create_payment_notifications, refresh_overdue_payments


class Command(BaseCommand):
    help = 'Actualiza pagos vencidos y crea notificaciones de recordatorio.'

    def handle(self, *args, **options):
        updated = refresh_overdue_payments()
        created = create_payment_notifications()
        self.stdout.write(self.style.SUCCESS(
            f'Pagos vencidos actualizados: {updated}. Notificaciones creadas: {created}.'
        ))
