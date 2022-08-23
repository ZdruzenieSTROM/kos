from django import forms
from django.contrib.auth.forms import AuthenticationForm


class RegisterForm(forms.Form):
    """Kos team registration form"""
    team_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Názov tímu')
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Heslo')
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Zopakuj heslo',)
    team_member_1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='1. člen tímu')
    team_member_2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='2. člen tímu', required=False)
    team_member_3 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='3. člen tímu', required=False)
    team_member_4 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='4. člen tímu', required=False)
    team_member_5 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='5. člen tímu', required=False
    )
    is_online = forms.BooleanField(
        label='Chcem riešiť online'
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
        self.fields['username'].label = 'Názov tímu'
        self.fields['password'].label = 'Heslo'


class ChangePasswordForm(forms.Form):
    """Form na zmenu hesla"""
    old_password = password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Staré heslo')
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Heslo')
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Zopakuj heslo',)

    def clean_password2(self):
        """Heslo a zopakované heslo sa rovnajú"""
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if not password2:
            raise forms.ValidationError("Musíte potvrdiť svoje heslo")
        if password1 != password2:
            raise forms.ValidationError("Heslá sa musia zhodovať")
        return password2


class EditTeamForm(forms.Form):
    """Form na úpravu tímových údajov"""
    team_member_1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='1. člen tímu')
    team_member_2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='2. člen tímu', required=False)
    team_member_3 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='3. člen tímu', required=False)
    team_member_4 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='4. člen tímu', required=False)
    team_member_5 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='5. člen tímu', required=False
    )
