from ast import Pass

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

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
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label='Chcem riešiť online'
    )
    # FIXME: Add ordering
    game = forms.ModelChoiceField(
        widget=forms.Select(attrs={'class': 'main-input'}),
        queryset=Game.objects.filter(
            year__in=Year.objects.filter(is_active=True, is_public=True)),
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


class ChangePasswordForm(PasswordChangeForm):
    """Lokalizovaný formulár pre zmenu hesla"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Staré heslo'
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['new_password1'].label = 'Zadajte nové heslo'
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['new_password2'].label = 'Zadajte znova nové heslo'
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'autofocus': True, 'class': 'main-input'})


class AuthForm(AuthenticationForm):
    """Lokalizovaný prihlasovací formulár"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Názov tímu'
        self.fields['username'].widget = forms.TextInput(
            attrs={'autofocus': True, 'class': 'main-input'})
        self.fields['password'].label = 'Heslo'
        self.fields['password'].widget = forms.PasswordInput(
            attrs={'autocomplete': 'current-password', 'class': 'main-input'})


# class ChangePasswordForm(forms.Form):
#     """Form na zmenu hesla"""
#     old_password = password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
#         label='Staré heslo')
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
#         label='Heslo')
#     password2 = forms.CharField(
#         widget=forms.PasswordInput(attrs={'class': 'form-control main-input'}),
#         label='Zopakuj heslo',)

#     def clean_password2(self):
#         """Heslo a zopakované heslo sa rovnajú"""
#         old_password = self.cleaned_data.get('old_password')
#         password1 = self.cleaned_data.get('password')
#         password2 = self.cleaned_data.get('password2')

#         if not password2:
#             raise forms.ValidationError("Musíte potvrdiť svoje heslo")
#         if password1 != password2:
#             raise forms.ValidationError("Heslá sa musia zhodovať")
#         return password2


class EditTeamForm(forms.Form):
    """Form na úpravu tímových údajov"""
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
