from django import forms
from django.forms import ModelChoiceField
from .models import Grade

    
class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    school  = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}), required=True)
    grade = ModelChoiceField(queryset=Grade.objects.all())

class AnswerForm(forms.Form):
    Odpoved = forms.FloatField(required=True)
    level = forms.IntegerField(widget=forms.HiddenInput())