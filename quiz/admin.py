from django.contrib import admin
from users.models import User
from .models import RepeatQuizQuestion, RepeatQuiz, RepeatQuizOption, SavedQuiz

admin.site.register(User)
admin.site.register(RepeatQuiz)
admin.site.register(SavedQuiz)
admin.site.register(RepeatQuizOption)
admin.site.register(RepeatQuizQuestion)