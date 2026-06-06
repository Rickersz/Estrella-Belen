from django.test import TestCase

from escuela.models import SchoolConfiguration
from .views import datos_institucionales


class ReportConfigurationTests(TestCase):
    def test_reportes_usan_configuracion_institucional(self):
        config = SchoolConfiguration.get_solo()
        config.institution_name = 'Colegio Configurado'
        config.director_name = 'Directora Configurada'
        config.director_document = 'V-123'
        config.rif = 'J-123'
        config.dea_code = 'DEA-123'
        config.report_footer = 'Pie configurado'
        config.save()

        data = datos_institucionales()

        self.assertEqual(data['institucion'], 'Colegio Configurado')
        self.assertEqual(data['directora'], 'Directora Configurada')
        self.assertEqual(data['directora_cedula'], 'V-123')
        self.assertEqual(data['rif'], 'J-123')
        self.assertEqual(data['dea'], 'DEA-123')
        self.assertEqual(data['footer'], 'Pie configurado')
