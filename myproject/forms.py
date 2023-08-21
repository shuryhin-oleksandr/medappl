from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
User = get_user_model()


class UserPasswordResetForm(SetPasswordForm):
    """Change password form."""
    new_password1 = forms.CharField(label='Password',
        help_text="<ul class='errorlist text-muted'><li>Vaše heslo nemôže byť podobné Vašim ostatným osobným údajom.</li><li>Vaše heslo musí mať aspoň 8 znakov.</li><li>Vaše heslo nemôže byť často používaným heslom.</li><li>Vaše heslo nemôže pozostávať iba z čísel.</li></ul>",
        max_length=100,
        required=True,
        widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'heslo',
            'type': 'password',
            'id': 'user_password',
        }))

    new_password2 = forms.CharField(label='Confirm password',
        help_text=False,
        max_length=100,
        required=True,
        widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'potvrdiť heslo',
            'type': 'password',
            'id': 'user_password',
        }))


class UserForgotPasswordForm(PasswordResetForm):
    """User forgot password, check via email form."""
    email = forms.EmailField(label='Email address',
        max_length=254,
        required=True,
        widget=forms.TextInput(
         attrs={'class': 'form-control',
                'placeholder': 'emailová adresa',
                'type': 'text',
                'id': 'email_address'
                }
        ))


class UserSignUpForm(UserCreationForm):
    """User registration form."""
    username = forms.CharField(label='Username',
        max_length=100,
        required=True,
        widget=forms.TextInput(
        attrs={'class': 'form-control',
               'placeholder': 'užívateľské meno',
               'type': 'text',
               'id': 'user_name'
               }
        ))


    email = forms.EmailField(label='Email address',
        max_length=254,
        required=True,
        widget=forms.TextInput(
        attrs={'class': 'form-control',
               'placeholder': 'emailová adresa',
               'type': 'text',
               'id': 'email_address'
               }
        ))

    password1 = forms.CharField(label='Password',
        help_text="<ul class='errorlist text-muted'><li>Vaše heslo nemôže byť podobné Vašim ostatným osobným údajom.</li><li>Vaše heslo musí mať aspoň 8 znakov.</li><li>Vaše heslo nemôže byť často používaným heslom.</li><li>Vaše heslo nemôže pozostávať iba z čísel.</li></ul>",
        max_length=100,
        required=True,
        widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'heslo',
            'type': 'password',
            'id': 'user_password',
        }))

    password2 = forms.CharField(label='Confirm password',
        help_text=False,
        max_length=100,
        required=True,
        widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'potvrdiť heslo',
            'type': 'password',
            'id': 'user_password',
        }))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', )

