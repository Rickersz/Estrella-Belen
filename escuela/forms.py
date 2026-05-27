from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from autenticacion.models import CustomUser
from estudiante.models import Parent
from .models import SchoolConfiguration

PASSWORD_HELP = 'Minimo 16 caracteres, con mayuscula, minuscula, numero y caracter especial.'


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Password', help_text=PASSWORD_HELP)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Confirm Password')
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password', 'is_admin', 'is_student', 'is_teacher', 'is_representative', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['password'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Las contrasenas no coinciden.')

        if password:
            user = CustomUser(
                email=cleaned_data.get('email') or '',
                first_name=cleaned_data.get('first_name') or '',
                last_name=cleaned_data.get('last_name') or '',
            )
            try:
                validate_password(password, user)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned_data

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'is_admin', 'is_student', 'is_teacher', 'is_representative', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SchoolConfigurationForm(forms.ModelForm):
    class Meta:
        model = SchoolConfiguration
        fields = [
            'institution_name', 'active_academic_year', 'director_name', 'rif',
            'dea_code', 'phone', 'email', 'address', 'payment_reminder_days',
        ]
        widgets = {
            'institution_name': forms.TextInput(attrs={'class': 'form-control'}),
            'active_academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'director_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rif': forms.TextInput(attrs={'class': 'form-control'}),
            'dea_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_reminder_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '30'}),
        }


class RepresentativeAccessForm(forms.Form):
    email = forms.EmailField(label='Correo de acceso', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Nombre', max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Apellido', max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        if parent and not self.is_bound:
            email = parent.father_email or parent.mother_email or ''
            full_name = parent.father_name or parent.mother_name or ''
            names = full_name.split()
            self.fields['email'].initial = email
            self.fields['first_name'].initial = names[0] if names else full_name
            self.fields['last_name'].initial = ' '.join(names[1:]) or 'Representante'


class InvitationPasswordForm(forms.Form):
    password = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text=PASSWORD_HELP)
    confirm_password = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm_password = cleaned.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Las contrasenas no coinciden.')
        if password:
            try:
                validate_password(password, self.user)
            except ValidationError as exc:
                self.add_error('password', exc)
        return cleaned
