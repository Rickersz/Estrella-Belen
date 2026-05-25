from django import forms

from .models import Enrollment, Parent, Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'first_name', 'last_name', 'student_class', 'tiene_cedula', 'cedula',
            'nacionalidad', 'estado_natal', 'edad', 'etnia', 'pais_extranjero', 'direccion_completa',
            'etapa', 'grado', 'section', 'admission_number', 'joining_date', 'gender', 'date_of_birth',
            'pantalon', 'camisa', 'calzado', 'peso', 'estatura', 'transporte', 'vive_con_padres',
            'huerfano', 'discapacidad', 'condicion', 'area_condicion', 'tipo_discapacidad',
            'carnet_discapacidad', 'informe_medico', 'recibe_tratamiento', 'cual_tratamiento',
            'plantel_anterior', 'repitiente', 'aula_integrada', 'cargado_sge', 'observaciones',
            'student_image',
        ]

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
            raise forms.ValidationError('Ya existe un estudiante con esta cédula escolar.')
        return student_id

    def clean_cedula(self):
        cedula = (self.cleaned_data.get('cedula') or '').strip()
        return cedula or None

    def clean_edad(self):
        edad = (self.cleaned_data.get('edad') or '').strip()
        if edad and not edad.isdigit():
            raise forms.ValidationError('La edad debe contener solo números.')
        return edad or None

    def clean(self):
        cleaned_data = super().clean()
        tiene_cedula = cleaned_data.get('tiene_cedula')
        cedula = cleaned_data.get('cedula')
        etapa = cleaned_data.get('etapa')
        grado = cleaned_data.get('grado')
        fecha_nacimiento = cleaned_data.get('date_of_birth')
        fecha_ingreso = cleaned_data.get('joining_date')

        if tiene_cedula and not cedula:
            self.add_error('cedula', 'Debe indicar la cédula de identidad.')

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

    def clean_father_name(self):
        return self.cleaned_data['father_name'].strip().title()

    def clean_mother_name(self):
        return self.cleaned_data['mother_name'].strip().title()

    def clean_father_mobile(self):
        mobile = self.cleaned_data['father_mobile'].strip()
        if len(mobile) < 7:
            raise forms.ValidationError('El teléfono del padre debe tener al menos 7 caracteres.')
        return mobile

    def clean_mother_mobile(self):
        mobile = self.cleaned_data['mother_mobile'].strip()
        if len(mobile) < 7:
            raise forms.ValidationError('El teléfono de la madre debe tener al menos 7 caracteres.')
        return mobile


class EnrollmentForm(forms.ModelForm):
    monto_inscripcion = forms.DecimalField(required=False, min_value=0, max_digits=12, decimal_places=2)

    class Meta:
        model = Enrollment
        fields = ['monto_inscripcion']

    def clean_monto_inscripcion(self):
        monto = self.cleaned_data.get('monto_inscripcion') or 0
        if monto < 0:
            raise forms.ValidationError('El monto de inscripción no puede ser negativo.')
        return monto
