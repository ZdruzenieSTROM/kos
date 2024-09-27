from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm, ResetPasswordKeyForm
from allauth.account.utils import filter_users_by_email
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.timezone import now

from kos.models import Game, Year


class RegisterForm(forms.Form):
    """Kos team registration form"""
    team_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Názov tímu')
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control main-input'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
        label='Heslo')
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
        label='Zopakuj heslo',)
    team_member_1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='1. člen tímu')
    team_member_2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='2. člen tímu', required=False)
    team_member_3 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='3. člen tímu', required=False)
    team_member_4 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='4. člen tímu', required=False)
    team_member_5 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='5. člen tímu', required=False
    )
    is_online = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label='Chcem riešiť online'
    )
    # FIXME: Add ordering
    game = forms.ModelChoiceField(
        widget=forms.Select(attrs={'class': 'main-input'}),
        queryset=Game.objects.filter(
            year__in=Year.objects.filter(is_active=True, is_public=True, registration_deadline__gte=now())),
        label='Kategória'
    )

    def clean_password2(self):
        """Heslo a zopakované heslo sa rovnajú"""
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("Musíte potvrdiť svoje heslo")
        if password1 != password2:
            raise forms.ValidationError("Heslá sa musia zhodovať")
        return password2


class AuthForm(AuthenticationForm):
    """Lokalizovaný prihlasovací formulár"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Login'
        self.fields['username'].widget = forms.TextInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['password'].label = 'Heslo'
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'autocomplete': 'current-password', 'class': 'main-input'})

        self.error_messages['invalid_login'] = 'Zadaný login alebo heslo bolo nesprávne.'


class ChangePasswordForm(PasswordChangeForm):
    """Lokalizovaný formulár pre zmenu hesla"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Staré heslo'
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['new_password1'].label = 'Nové heslo'
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'class': 'main-input'})
        self.fields['new_password2'].label = 'Nové heslo (znova)'
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'class': 'main-input'})

        self.error_messages = {
            "password_incorrect": "Zadané heslo bolo nesprávne",
            "password_mismatch": "Heslá sa musia zhodovať"
        }


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Email'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['email'].widget.attrs['class'] = 'main-input'

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)
        self.users = filter_users_by_email(email, is_active=True)
        if not self.users and not app_settings.PREVENT_ENUMERATION:
            raise forms.ValidationError(
                ("Na tento email nie je registrovaný žiaden účet alebo tento email ešte nebol potvrdený.")
            )
        return self.cleaned_data["email"]


class CustomResetPasswordFromKey(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Nové heslo'
        self.fields['password2'].label = 'Nové heslo (znova)'
        self.fields['password1'].widget.attrs['placeholder'] = 'Nové heslo'
        self.fields['password1'].widget.attrs['class'] = 'main-input'
        self.fields['password2'].widget.attrs['placeholder'] = 'Nové heslo (znova)'
        self.fields['password2'].widget.attrs['class'] = 'main-input'


class EditTeamForm(forms.Form):
    """Form na úpravu tímových údajov"""
    team_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='Názov tímu')
    team_member_1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='1. člen tímu')
    team_member_2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='2. člen tímu', required=False)
    team_member_3 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='3. člen tímu', required=False)
    team_member_4 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='4. člen tímu', required=False)
    team_member_5 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control main-input'}),
        label='5. člen tímu', required=False
    )
    is_online = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label='Chcem riešiť online'
    )
