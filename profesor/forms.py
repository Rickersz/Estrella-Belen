from django import forms

from escuela.validators import validate_phone
from .models import Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'teacher_id', 'name', 'gender', 'date_of_birth', 'joining_date', 'mobile_number',
            'qualification', 'experience', 'teacher_image', 'email', 'address', 'city', 'state',
            'country', 'zip_code', 'department', 'subjects',
        ]

    def clean_teacher_id(self):
        teacher_id = self.cleaned_data['teacher_id'].strip()
        queryset = Teacher.objects.filter(teacher_id__iexact=teacher_id)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ya existe un profesor con este identificador.')
        return teacher_id

    def clean_name(self):
        return self.cleaned_data['name'].strip().title()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        queryset = Teacher.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ya existe un profesor con este correo.')
        return email

    def clean_mobile_number(self):
        mobile = validate_phone(self.cleaned_data['mobile_number'], 'telefono')
        if len(mobile) < 7:
            raise forms.ValidationError('El telefono debe tener al menos 7 caracteres.')
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        joining_date = cleaned_data.get('joining_date')
        if date_of_birth and joining_date and joining_date < date_of_birth:
            self.add_error('joining_date', 'La fecha de ingreso no puede ser anterior al nacimiento.')
        return cleaned_data
