from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.db.models import Q

class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-postadress",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'namn@epost.se',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label="Lösenord",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    def clean(self):
        login_input = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if login_input and password:
            User = get_user_model()
            user_obj = User.objects.filter(
                Q(email__iexact=login_input) | Q(username__iexact=login_input)
            ).first()

            if user_obj:
                self.cleaned_data['username'] = user_obj.username

        return super().clean()