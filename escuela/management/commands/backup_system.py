from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'Crea un backup zip de db.sqlite3 y media/.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='backups', help='Directorio destino del backup.')

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        db_path = Path(settings.DATABASES['default']['NAME'])
        media_root = Path(settings.MEDIA_ROOT)
        output_dir = Path(options['output_dir'])
        if not output_dir.is_absolute():
            output_dir = base_dir / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        if not db_path.exists():
            raise CommandError(f'No existe la base de datos: {db_path}')

        timestamp = timezone.localtime().strftime('%Y%m%d_%H%M%S')
        backup_path = output_dir / f'estrella_belen_backup_{timestamp}.zip'

        with ZipFile(backup_path, 'w', ZIP_DEFLATED) as archive:
            archive.write(db_path, arcname=db_path.name)
            if media_root.exists():
                for file_path in media_root.rglob('*'):
                    if file_path.is_file():
                        archive.write(file_path, arcname=str(Path('media') / file_path.relative_to(media_root)))

        self.stdout.write(self.style.SUCCESS(f'Backup creado: {backup_path}'))
