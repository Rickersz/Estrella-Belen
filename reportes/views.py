from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import ConstanciaForm
from .models import Constancia
from escuela.models import SchoolConfiguration
from estudiante.models import Student


DIRECTORA = 'Directora'
DIRECTORA_CEDULA = ''
INSTITUCION = 'Unidad Educativa Estrella de Belen'
CODIGO_DEA = ''
RIF = ''
LUGAR = 'Bella Vista'
DIRECCION_FOOTER = ''

MESES = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]

UNIDADES = [
    'cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho',
    'nueve', 'diez', 'once', 'doce', 'trece', 'catorce', 'quince',
    'dieciseis', 'diecisiete', 'dieciocho', 'diecinueve'
]

DECENAS = {
    20: 'veinte', 30: 'treinta', 40: 'cuarenta', 50: 'cincuenta',
    60: 'sesenta', 70: 'setenta', 80: 'ochenta', 90: 'noventa'
}

CENTENAS = {
    100: 'cien', 200: 'doscientos', 300: 'trescientos', 400: 'cuatrocientos',
    500: 'quinientos', 600: 'seiscientos', 700: 'setecientos',
    800: 'ochocientos', 900: 'novecientos'
}


def can_manage_constancias(user):
    return (hasattr(user, 'is_admin') and user.is_admin) or (hasattr(user, 'is_teacher') and user.is_teacher)


def representative_parent(user):
    if hasattr(user, 'is_representative') and user.is_representative:
        return getattr(user, 'representante', None)
    return None


def can_view_student_reports(user, student):
    if can_manage_constancias(user):
        return True
    parent = representative_parent(user)
    return bool(parent and student.parent_id == parent.id)


def can_view_constancia(user, constancia):
    return can_view_student_reports(user, constancia.student)


def numero_a_letras(numero):
    numero = int(numero)
    if numero < 20:
        return UNIDADES[numero]
    if numero < 30:
        return 'veinti' + UNIDADES[numero - 20] if numero > 20 else DECENAS[20]
    if numero < 100:
        decena = (numero // 10) * 10
        unidad = numero % 10
        return DECENAS[decena] if unidad == 0 else f'{DECENAS[decena]} y {UNIDADES[unidad]}'
    if numero < 1000:
        centena = (numero // 100) * 100
        resto = numero % 100
        if numero == 100:
            return 'cien'
        prefijo = 'ciento' if centena == 100 else CENTENAS[centena]
        return prefijo if resto == 0 else f'{prefijo} {numero_a_letras(resto)}'
    if numero < 1000000:
        miles = numero // 1000
        resto = numero % 1000
        prefijo = 'mil' if miles == 1 else f'{numero_a_letras(miles)} mil'
        return prefijo if resto == 0 else f'{prefijo} {numero_a_letras(resto)}'
    return str(numero)


def monto_en_letras(monto):
    if monto is None:
        return ''
    monto = Decimal(monto).quantize(Decimal('0.01'))
    enteros = int(monto)
    centimos = int((monto - enteros) * 100)
    return f'{numero_a_letras(enteros).title()} con {centimos:02d} centimos'


def fecha_larga(fecha):
    return f'{fecha.day} dias del mes de {MESES[fecha.month]} del ano dos mil {numero_a_letras(fecha.year - 2000).title()}'


def nombre_estudiante(student):
    return f'{student.first_name} {student.last_name}'.upper()


def documento_estudiante(student):
    if student.cedula:
        return f'Cedula de Identidad Nro {student.cedula}'
    return f'Cedula Escolar Nro {student.student_id}'


def lugar_nacimiento(student):
    return student.estado_natal or student.pais_extranjero or 'Punto Fijo Estado Falcon'


def grado_texto(constancia):
    student = constancia.student
    grado = student.grado or student.student_class or ''
    etapa = student.etapa or ''
    if etapa:
        return f'{grado} de Educacion {etapa}'
    return grado


def representante(constancia):
    if constancia.representative_name:
        return constancia.representative_name.upper(), constancia.representative_id or ''
    parent = getattr(constancia.student, 'parent', None)
    if parent:
        if parent.mother_name:
            return parent.mother_name.upper(), parent.cedula_padre or ''
        if parent.father_name:
            return parent.father_name.upper(), parent.cedula_padre or ''
    return 'REPRESENTANTE', constancia.representative_id or ''


def datos_institucionales():
    config = SchoolConfiguration.get_solo()
    return {
        'directora': config.director_name or DIRECTORA,
        'directora_cedula': config.director_document or DIRECTORA_CEDULA,
        'institucion': config.institution_name or INSTITUCION,
        'dea': config.dea_code or CODIGO_DEA,
        'rif': config.rif or RIF,
        'footer': config.report_footer or config.address or DIRECCION_FOOTER,
    }


def cuerpo_constancia(constancia, institucion=None):
    student = constancia.student
    institucion = institucion or datos_institucionales()
    cedula_directora = f', titular de la cedula de Identidad Nro <b>{institucion["directora_cedula"]}</b>,' if institucion['directora_cedula'] else ''
    base = (
        f'Quien suscribe, <b><i>{institucion["directora"]}</i></b>{cedula_directora} '
        f'hace constar por medio de la presente que el (la) '
    )

    if constancia.report_type == Constancia.TIPO_SOLVENCIA:
        nombre_rep, cedula_rep = representante(constancia)
        cedula = f' titular de la Cedula de Identidad Nro <b>{cedula_rep}</b>' if cedula_rep else ''
        periodo = constancia.solvent_until or constancia.academic_year
        return (
            f'{base}Representante: <b><u>{nombre_rep}</u></b>{cedula}, cumplio con los compromisos '
            f'adquiridos de pago mensuales. Esta <b><u>"SOLVENTE"</u></b> hasta el {periodo}.'
        )

    if constancia.report_type == Constancia.TIPO_ESTUDIO:
        return (
            f'{base}nino (a): <b><u>{nombre_estudiante(student)}</u></b>, Titular de la '
            f'{documento_estudiante(student)}, nacido (a) en <b>{lugar_nacimiento(student)}</b> '
            f'el dia {student.date_of_birth.day} de {MESES[student.date_of_birth.month]} del ano '
            f'{student.date_of_birth.year}, fue inscrito (a) en esta institucion para cursar '
            f'<b><u>"{grado_texto(constancia).upper()}"</u></b> durante el ano Escolar {constancia.academic_year}.'
        )

    if constancia.report_type == Constancia.TIPO_COMPORTAMIENTO:
        return (
            f'{base}nino (a): <b><u>{nombre_estudiante(student)}</u></b>, Titular de la '
            f'{documento_estudiante(student)}, nacido (a) en <b>{lugar_nacimiento(student)}</b> '
            f'el dia {student.date_of_birth.day} de {MESES[student.date_of_birth.month]} del ano '
            f'{student.date_of_birth.year}, fue inscrito (a) en esta institucion para cursar '
            f'<b><u>{grado_texto(constancia)}</u></b> durante el ano escolar {constancia.academic_year} '
            f'y demostro comportamiento: <b><u>{constancia.behavior_rating}</u></b>.'
        )

    monto = constancia.amount_paid
    monto_texto = ''
    if monto is not None:
        monto_texto = f'<br/><br/>Cancelando un monto de <b>{monto_en_letras(monto)}</b> ({monto:,.2f}).'
    return (
        f'{base}nino (a): <b><u>{nombre_estudiante(student)}</u></b>, Titular de la '
        f'{documento_estudiante(student)}, nacido (a) en <b>{lugar_nacimiento(student)}</b> '
        f'el dia {student.date_of_birth.day} de {MESES[student.date_of_birth.month]} del ano '
        f'{student.date_of_birth.year}, fue inscrito (a) en esta institucion para cursar '
        f'<b><u>"{grado_texto(constancia).upper()}"</u></b> durante el ano Escolar {constancia.academic_year}.'
        f'{monto_texto}'
    )


def titulo_constancia(constancia):
    return dict(Constancia.TIPO_CHOICES).get(constancia.report_type, constancia.title)


def generar_pdf_constancia(constancia):
    institucion = datos_institucionales()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.95 * inch,
        leftMargin=0.95 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='HeaderText', parent=styles['Normal'], fontName='Times-Italic', fontSize=10, leading=12))
    styles.add(ParagraphStyle(name='DocTitle', parent=styles['Title'], fontName='Times-Bold', fontSize=25, leading=32, alignment=TA_CENTER, textColor=colors.HexColor('#444444'), spaceAfter=36))
    styles.add(ParagraphStyle(name='BodyTextJustify', parent=styles['Normal'], fontName='Times-Italic', fontSize=13, leading=28, alignment=TA_JUSTIFY, firstLineIndent=28))
    styles.add(ParagraphStyle(name='BodyLeft', parent=styles['Normal'], fontName='Times-Italic', fontSize=13, leading=24, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='CenterSmall', parent=styles['Normal'], fontName='Times-Italic', fontSize=11, alignment=TA_CENTER))

    logo_path = Path(settings.BASE_DIR) / 'static' / 'assets' / 'img' / 'logo.png'
    if logo_path.exists():
        logo = Image(str(logo_path), width=1.05 * inch, height=1.05 * inch)
    else:
        logo = Paragraph('', styles['Normal'])

    header_text = (
        f'<b>{institucion["institucion"]}</b><br/>'
        'Ministerio del Poder Popular Para La Educacion.<br/>'
        f'Codigo DEA: {institucion["dea"] or "-"}<br/>'
        'Republica Bolivariana de Venezuela<br/>'
        f'RIF: {institucion["rif"] or "-"}'
    )
    header = Table([[logo, Paragraph(header_text, styles['HeaderText'])]], colWidths=[1.25 * inch, 4.7 * inch])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (0, 0), 1, colors.black),
    ]))

    story = [
        header,
        Spacer(1, 0.65 * inch),
        Paragraph(titulo_constancia(constancia) + '.', styles['DocTitle']),
        Paragraph(cuerpo_constancia(constancia, institucion), styles['BodyTextJustify']),
        Spacer(1, 0.45 * inch),
        Paragraph(f'En {LUGAR} a los {fecha_larga(timezone.localdate())}.', styles['BodyLeft']),
    ]

    if constancia.report_type == Constancia.TIPO_COMPORTAMIENTO:
        story.extend([
            Spacer(1, 0.22 * inch),
            Paragraph('&bull; Excelente.<br/>&bull; Distinguido.<br/>&bull; Suficiente.', styles['BodyLeft']),
        ])

    story.extend([
        Spacer(1, 0.9 * inch),
        Paragraph(f'______________________________<br/><b>{institucion["directora"]}</b><br/>Directora.', styles['CenterSmall']),
        Spacer(1, 0.35 * inch),
        Paragraph(institucion['footer'], styles['CenterSmall']),
    ])

    doc.build(story)
    buffer.seek(0)
    return buffer


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_constancias, login_url='iniciar_sesion')
def reportes_home(request):
    constancias = Constancia.objects.select_related('student', 'issued_by').all()
    query = request.GET.get('q', '').strip()

    if query:
        constancias = constancias.filter(
            student__first_name__icontains=query
        ) | constancias.filter(
            student__last_name__icontains=query
        ) | constancias.filter(
            student__student_id__icontains=query
        ) | constancias.filter(
            title__icontains=query
        )

    return render(request, 'reportes/index.html', {
        'constancias': constancias.distinct(),
        'query': query,
        'total': constancias.count(),
    })


@login_required(login_url='iniciar_sesion')
@user_passes_test(can_manage_constancias, login_url='iniciar_sesion')
def constancia_create(request):
    if request.method == 'POST':
        form = ConstanciaForm(request.POST)
        if form.is_valid():
            constancia = form.save(commit=False)
            constancia.title = titulo_constancia(constancia)
            constancia.issued_by = request.user
            constancia.save()
            return redirect('constancia_detail', pk=constancia.pk)
    else:
        form = ConstanciaForm()
    return render(request, 'reportes/constancia_form.html', {'form': form})


@login_required(login_url='iniciar_sesion')
def constancia_detail(request, pk):
    constancia = get_object_or_404(Constancia.objects.select_related('student', 'student__parent', 'issued_by'), pk=pk)
    if not can_view_constancia(request.user, constancia):
        return HttpResponseForbidden('No tienes permiso para descargar esta constancia.')
    pdf = generar_pdf_constancia(constancia)
    filename = f'{constancia.report_type}_{constancia.student.student_id}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url='iniciar_sesion')
def representative_reports(request):
    parent = representative_parent(request.user)
    if not parent:
        return HttpResponseForbidden('No tienes un representante asociado a este usuario.')

    students = Student.objects.filter(parent=parent, is_archived=False).order_by('first_name', 'last_name')
    selected_student = None
    student_id = request.GET.get('student')
    if student_id:
        selected_student = students.filter(pk=student_id).first()
    if selected_student is None:
        selected_student = students.first()

    constancias = Constancia.objects.filter(student__parent=parent).select_related('student', 'issued_by')
    if selected_student:
        constancias = constancias.filter(student=selected_student)

    return render(request, 'reportes/representante.html', {
        'parent': parent,
        'students': students,
        'selected_student': selected_student,
        'constancias': constancias,
        'constancia_types': [
            (Constancia.TIPO_ESTUDIO, 'Constancia de estudio', 'fa-file-signature'),
            (Constancia.TIPO_INSCRIPCION, 'Constancia de inscripcion', 'fa-file-lines'),
            (Constancia.TIPO_COMPORTAMIENTO, 'Certificado de comportamiento', 'fa-award'),
        ],
    })


@login_required(login_url='iniciar_sesion')
def representative_constancia_pdf(request, student_id, report_type):
    parent = representative_parent(request.user)
    if not parent:
        return HttpResponseForbidden('No tienes un representante asociado a este usuario.')

    valid_types = {choice[0] for choice in Constancia.TIPO_CHOICES}
    if report_type not in valid_types:
        return HttpResponseForbidden('Tipo de constancia invalido.')

    student = get_object_or_404(Student.objects.select_related('parent'), pk=student_id, parent=parent, is_archived=False)
    config = SchoolConfiguration.get_solo()
    constancia = Constancia.objects.create(
        report_type=report_type,
        title=dict(Constancia.TIPO_CHOICES).get(report_type, 'Constancia'),
        student=student,
        issued_by=request.user,
        academic_year=config.active_academic_year,
    )
    pdf = generar_pdf_constancia(constancia)
    filename = f'{constancia.report_type}_{student.student_id}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
