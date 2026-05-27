from django import forms

from .models import AcademicGrade, Announcement, ClassSchedule, CommunicationMessage, DisciplineObservation, SchoolEvent


class AcademicGradeForm(forms.ModelForm):
    class Meta:
        model = AcademicGrade
        fields = ['student', 'subject', 'teacher', 'academic_year', 'period', 'grade', 'weight', 'qualitative', 'notes', 'is_locked']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '20'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1', 'max': '100'}),
            'qualitative': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_locked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_grade(self):
        grade = self.cleaned_data['grade']
        if grade < 0 or grade > 20:
            raise forms.ValidationError('La nota debe estar entre 0 y 20.')
        return grade

    def clean_weight(self):
        weight = self.cleaned_data['weight']
        if weight <= 0 or weight > 100:
            raise forms.ValidationError('La ponderacion debe estar entre 1 y 100.')
        return weight


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = ['class_assigned', 'subject', 'teacher', 'day', 'start_time', 'end_time', 'classroom']
        widgets = {
            'class_assigned': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'classroom': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SchoolEventForm(forms.ModelForm):
    class Meta:
        model = SchoolEvent
        fields = ['title', 'description', 'event_type', 'start_date', 'end_date', 'audience']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'audience': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DisciplineObservationForm(forms.ModelForm):
    class Meta:
        model = DisciplineObservation
        fields = ['student', 'teacher', 'date', 'severity', 'description', 'action_taken']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'action_taken': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'audience', 'send_email', 'send_whatsapp']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'audience': forms.Select(attrs={'class': 'form-control'}),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_whatsapp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommunicationMessageForm(forms.ModelForm):
    class Meta:
        model = CommunicationMessage
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
