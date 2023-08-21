from django import forms
from users.models import User
from django.forms import ValidationError
from django.contrib.auth.forms import UserCreationForm

def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.txt']

    if not ext.lower() in valid_extensions:
        raise ValidationError(
            'Unsupported file extension. The file should be a text file.')

def file_size(value):
    sizeInMB = 1
    limit = sizeInMB * 1024 * 1024

    if value.size > limit:
        raise ValidationError(
            f'File too large. Size should not exceed {sizeInMB} MB.')

class CustomQuizForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    number_of_questions = forms.IntegerField(min_value=1, max_value=1500, required=True)
    options_per_questions = forms.IntegerField(min_value=1, max_value=8, required=True)
    negativeMarking = forms.IntegerField(min_value=0, max_value=1, required=True)
    questions = forms.FileField(required=False, validators=[validate_file_extension, file_size])
    answers = forms.FileField(validators=[validate_file_extension, file_size], error_messages={
        "required": 'No answer key file provided'
    })

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields