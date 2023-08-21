from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from .views import general_quiz, create_user, loginStatusView, HomeView, repeat_quiz_save_options, update_repeat_quiz_name, repeat_quiz, delete_repeat_quiz_questions, custom_quiz, exam_creator, lfuk, contact, delete_saved_quiz, update_saved_quiz_name, saved_quiz, repeat_quiz_delete_options

app_name = "quiz"
urlpatterns = [
    # Home
    path("", HomeView.as_view(), name='home'),
    path("exam-creator", exam_creator, name="exam-creator"),
    path("lfuk", lfuk, name="lfuk"),
    path("contact", contact, name="contact"),

    # Quiz
    path("quiz/save-options/", repeat_quiz_save_options, name="save-options"),
    path("quiz/delete-options/", repeat_quiz_delete_options, name="delete-options"),

    # General Quiz
    path("quiz/general/<mode>/", general_quiz, name="general-quiz"),

    # Custom Quiz
    path("quiz/custom/<mode>/", custom_quiz, name="custom-quiz"),

    # Saved Quiz
    path("quiz/saved-quiz/<slug:slug>/<int:mode>", saved_quiz, name="saved-quiz"),
    path("quiz/saved-quiz/delete/<slug:slug>/", delete_saved_quiz, name="delete-saved-quiz"),
    path("quiz/saved-quiz/update/name/", update_saved_quiz_name, name="save-saved-quiz-name"),

    # Repeat Quiz
    path("quiz/repeat-quiz/<slug:slug>/<int:mode>", repeat_quiz, name="repeat-quiz"),
    path("quiz/repeat-quiz/delete/<slug:slug>/", delete_repeat_quiz_questions, name="delete-repeat-quiz-questions"),
    path("quiz/repeat-quiz/update/name/", update_repeat_quiz_name, name="save-repeat-quiz-name"),

    # User
    path("user/create/", create_user, name="register"),
    path("user/login-status/", loginStatusView, name="login_status"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)