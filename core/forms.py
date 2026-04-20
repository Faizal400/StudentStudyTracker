from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=20)
    email = forms.EmailField(required=True)
    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("That email is already registered.")
        return email

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class LowercaseAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()