from django import forms

from escuela.validators import validate_academic_year, validate_phone
from .models import AttendanceRecord, Enrollment, GradeSectionCapacity, Parent, Student, StudentDocumentChecklist, StudentHealthRecord


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'student_class', 'tiene_cedula', 'cedula',
            'nacionalidad', 'estado_natal', 'etnia', 'pais_extranjero', 'direccion_completa',
            'etapa', 'grado', 'section', 'admission_number', 'joining_date', 'gender', 'date_of_birth',
            'pantalon', 'camisa', 'calzado', 'peso', 'estatura', 'transporte', 'vive_con_padres',
            'huerfano', 'discapacidad', 'condicion', 'area_condicion', 'tipo_discapacidad',
            'carnet_discapacidad', 'informe_medico', 'recibe_tratamiento', 'cual_tratamiento',
            'plantel_anterior', 'repitiente', 'aula_integrada', 'cargado_sge', 'observaciones',
            'student_image',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css_class} form-check-input'.strip()
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = f'{css_class} form-control'.strip()
            else:
                field.widget.attrs['class'] = f'{css_class} form-control'.strip()
        for name in ('date_of_birth', 'joining_date'):
            if name in self.fields:
                self.fields[name].widget.input_type = 'date'

    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip().title()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip().title()

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id'].strip()
        queryset = Student.objects.filter(student_id__iexact=student_id)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ya existe un estudiante con esta cedula escolar.')
        return student_id

    def clean_cedula(self):
        cedula = (self.cleaned_data.get('cedula') or '').strip()
        return cedula or None

    def clean(self):
        cleaned_data = super().clean()
        tiene_cedula = cleaned_data.get('tiene_cedula')
        cedula = cleaned_data.get('cedula')
        etapa = cleaned_data.get('etapa')
        grado = cleaned_data.get('grado')
        fecha_nacimiento = cleaned_data.get('date_of_birth')
        fecha_ingreso = cleaned_data.get('joining_date')

        if tiene_cedula and not cedula:
            self.add_error('cedula', 'Debe indicar la cedula de identidad.')

        grados_por_etapa = {
            'Preescolar': {'1er', '2do', '3er'},
            'Primaria': {'1ro', '2do', '3ro', '4to', '5to', '6to'},
        }
        if etapa and grado and grado not in grados_por_etapa.get(etapa, set()):
            self.add_error('grado', 'El grado seleccionado no corresponde con la etapa.')

        if fecha_nacimiento and fecha_ingreso and fecha_ingreso < fecha_nacimiento:
            self.add_error('joining_date', 'La fecha de ingreso no puede ser anterior al nacimiento.')

        return cleaned_data


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = [
            'father_name', 'father_mobile', 'father_email', 'mother_name', 'mother_mobile',
            'mother_email', 'cedula_padre', 'fechan_padre', 'trabaja_padre', 'lugar_trabajo_padre',
            'fechan_madre', 'trabaja_madre', 'lugar_trabajo_madre',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{css_class} form-check-input'.strip()
            else:
                field.widget.attrs['class'] = f'{css_class} form-control'.strip()
        for name in ('fechan_padre', 'fechan_madre'):
            if name in self.fields:
                self.fields[name].widget.input_type = 'date'

    def clean_father_name(self):
        return self.cleaned_data['father_name'].strip().title()

    def clean_mother_name(self):
        return self.cleaned_data['mother_name'].strip().title()

    def clean_father_mobile(self):
        mobile = validate_phone(self.cleaned_data['father_mobile'], 'telefono del padre')
        if len(mobile) < 7:
            raise forms.ValidationError('El telefono del padre debe tener al menos 7 caracteres.')
        return mobile

    def clean_mother_mobile(self):
        mobile = validate_phone(self.cleaned_data['mother_mobile'], 'telefono de la madre')
        if len(mobile) < 7:
            raise forms.ValidationError('El telefono de la madre debe tener al menos 7 caracteres.')
        return mobile


class EnrollmentForm(forms.ModelForm):
    monto_inscripcion = forms.DecimalField(required=False, min_value=0, max_digits=12, decimal_places=2)

    class Meta:
        model = Enrollment
        fields = ['monto_inscripcion']

    def clean_monto_inscripcion(self):
        monto = self.cleaned_data.get('monto_inscripcion') or 0
        if monto < 0:
            raise forms.ValidationError('El monto de inscripcion no puede ser negativo.')
        return monto


class GradeSectionCapacityForm(forms.ModelForm):
    class Meta:
        model = GradeSectionCapacity
        fields = ['academic_year', 'etapa', 'grado', 'section', 'capacity']
        widgets = {
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'etapa': forms.TextInput(attrs={'class': 'form-control'}),
            'grado': forms.TextInput(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean_academic_year(self):
        return validate_academic_year(self.cleaned_data['academic_year'])


class StudentDocumentChecklistForm(forms.ModelForm):
    class Meta:
        model = StudentDocumentChecklist
        fields = [
            'birth_certificate', 'identity_card_copy', 'representative_id_copy',
            'student_photos', 'previous_school_certificate', 'vaccination_card',
            'medical_report', 'authorizations', 'notes',
        ]
        widgets = {'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}


class StudentHealthRecordForm(forms.ModelForm):
    class Meta:
        model = StudentHealthRecord
        fields = [
            'allergies', 'medications', 'emergency_contact_name', 'emergency_contact_phone',
            'medical_insurance', 'special_condition', 'important_notes',
        ]
        widgets = {
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_insurance': forms.TextInput(attrs={'class': 'form-control'}),
            'special_condition': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'important_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['student', 'date', 'academic_year', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_academic_year(self):
        return validate_academic_year(self.cleaned_data['academic_year'])


class SchoolYearClosureForm(forms.Form):
    current_academic_year = forms.CharField(label='Ano escolar actual', max_length=9, widget=forms.TextInput(attrs={'class': 'form-control'}))
    next_academic_year = forms.CharField(label='Proximo ano escolar', max_length=9, widget=forms.TextInput(attrs={'class': 'form-control'}))
    default_section = forms.CharField(label='Seccion por defecto', max_length=15, initial='A', widget=forms.TextInput(attrs={'class': 'form-control'}))
    close_grades = forms.BooleanField(label='Bloquear notas del ano cerrado', required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean_current_academic_year(self):
        return validate_academic_year(self.cleaned_data['current_academic_year'])

    def clean_next_academic_year(self):
        return validate_academic_year(self.cleaned_data['next_academic_year'])
