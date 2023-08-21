import json
from django.contrib import messages
from .models import RepeatQuiz, SavedQuiz, RepeatQuizQuestion, RepeatQuizOption
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from users.models import Subscription, UserSubscription
from django.contrib.auth.decorators import login_required
from .forms import CustomQuizForm, MyUserCreationForm
from .utils import get_general_quiz_data, get_repeat_quiz_data, generate_questions_file_template_data, get_saved_quiz_data, validate_custom_quiz_data, return_to_previous_url


subjectMapping = {
    "b": "biology",
    "c": "chemistry"
}

languages = {
    "slovak1": ["Slovak 1", "SK 1"],
    "slovak2": ["Slovak 2", "SK 2"],
    "czech2": ["Czech 1", "CZ 1"],
    "czech2": ["Czech 2", "CZ 2"],
    "english1": ["English 1", "EN 1"],
    "english2": ["English 2", "EN 2"],
    "no-audio": ["No Audio", "NA"]
}

# Colors - [backgrund, text]
saved_quiz_colors = [
    ["#FF0000", "#FFFFFF"], # red
    ["#FFFF00", "#000000"], # yellow
    ["#0080FF", "#FFFFFF"], # blue
    ["#00CC00", "#FFFFFF"], # green
    ["#0D0D0D", "#FFFFFF"], # black
]

general_quiz_colors = [
    ["#00CC00", "#FFFFFF"], # green - biology
    ["#0080FF", "#FFFFFF"], # blue - chemistry
]

subjects = {
    "biology": "Bio",
    "chemistry": "Chem"
}

class HomeView(TemplateView):
    template_name = "home.html"

@login_required
def exam_creator(request):
    repeat_quizzes = request.user.repeat_quizzes.all().filter(quiz_type__in=["SAVED"])
    saved_quizzes = request.user.saved_quizzes.all().filter(quiz_type="CUSTOM")

    saved_quizzes_count = request.user.saved_quizzes.all().filter(quiz_type="CUSTOM").count()

    form_1 = CustomQuizForm()
    error_custom_quiz = True

    if request.method == "GET":
        error_custom_quiz = False
    elif saved_quizzes_count >= 5:
        messages.error(request, "Saved exam limit reached. Only 5 saved exams can be added.")
    elif request.method == "POST" and saved_quizzes_count < 5:
        print("POST DATA:", request.POST)
        
        post = request.POST.copy()

        quiz_type = post["quiz_type"]
        post["voice_recognition"] = True if post["voiceRecognition"] == "1" else False

        if quiz_type.startswith("cq"): # Custom Quiz
            post["negative_marking"] = int(post["negativeMarking"])
            options_per_questions = int(post["options_per_questions"])
            number_of_questions = int(post["number_of_questions"])

            form_1 = CustomQuizForm(post, request.FILES)

            if form_1.is_valid():
                if (form_1.cleaned_data["questions"] is None):
                    questions_file_data = generate_questions_file_template_data(number_of_questions, options_per_questions)
                else:
                    questions_file_data = form_1.cleaned_data["questions"].read().decode("utf-8")

                answer_key_file_data = form_1.cleaned_data["answers"].read().decode("utf-8")

                data = validate_custom_quiz_data(questions_file_data, answer_key_file_data, number_of_questions, options_per_questions)

                if isinstance(data, list):
                    form_1.add_error(data[0], data[1])
                else:
                    if SavedQuiz.objects.filter(name=post["name"], quiz_type="CUSTOM", user=request.user).exists():
                        form_1.add_error("name", "Unique name required for the quiz.")
                    else:
                        # Saving Quiz Configuration
                        saved_quiz = SavedQuiz.objects.create(
                            name=post["name"],
                            quiz_type="CUSTOM",
                            user=request.user,
                            voice_recognition=post["voice_recognition"],
                            negative_marking=post["negative_marking"] == 1,
                            language=post["language"],
                            number_of_questions=number_of_questions,
                            number_of_options_per_question=options_per_questions,
                            questions=form_1.cleaned_data["questions"],
                            answers=form_1.cleaned_data["answers"]
                        )

                        repeat_quiz = RepeatQuiz.objects.create(
                            name=saved_quiz.name,
                            quiz_type="SAVED",
                            user=request.user,
                            parent_slug=saved_quiz.slug
                        )

                        # Renewing the form
                        form_1 = CustomQuizForm()
                        error_custom_quiz = False
            else:
                print('Errors Form #1:', form_1.errors)

    return render(request, "exam-creator.html", {
        "form": form_1,
        "error_custom_quiz": error_custom_quiz,
        "repeat_quizzes": list(zip(repeat_quizzes, saved_quiz_colors[:repeat_quizzes.count()])),
        "saved_quizzes": list(zip(saved_quizzes, saved_quiz_colors[:saved_quizzes.count()])),
    })

@login_required
def lfuk(request):
    repeat_quizzes = request.user.repeat_quizzes.all().filter(quiz_type="GENERAL")
    return render(request, "lfuk.html", {
        "repeat_quizzes": list(zip(repeat_quizzes, general_quiz_colors)),
        "general_quiz_colors": general_quiz_colors
    })

@login_required
def contact(request):
    return render(request, "contact.html", {})

def create_user(request):
    if request.user.is_superuser:
        if request.method == "GET":
            form = MyUserCreationForm()
        elif request.method == "POST":
            form = MyUserCreationForm(request.POST)
            
            if form.is_valid():
                user = form.save()
                FREE_SUBSCRIPTION = Subscription.objects.get(name="free")
                UserSubscription.objects.create(
                    user=user,
                    subscription=FREE_SUBSCRIPTION
                )
                return redirect("/admin/")
        return render(request, "registration/register.html", {"form": form})
    return render(request, "registration/register.html", {"error": "You don't have access to this page"})

@login_required
def custom_quiz(request, mode):
    if (request.session.has_key("custom_quiz_context")):
        context = request.session["custom_quiz_context"].copy()
        del request.session["custom_quiz_context"]

        if "source" in context.keys() and context["source"] == "SERVER_REDIRECT":
            return render(request, "quiz.html", context)

    return redirect("/quiz/")

@login_required
def general_quiz(request, mode):
    """
    View for general quiz
    """

    if request.method == "GET":
        return redirect("/lfuk")
        
    print("\nPOST DATA:", request.POST)
    print("MODE:", mode, end="\n\n")

    start = 1
    mode = int(mode)

    # if (not request.user.subscription.subscription.is_premium()) and (mode in [3, 4]):
    #     return HttpResponse("This route is reserved for premium users!")

    voice_recognition = request.POST.get('voiceRecognition', None)
    voice_recognition = False if (voice_recognition is None or voice_recognition == "0") else True

    if mode == 2 or mode == 4:
        start = int(request.POST['start'])

    subject = request.POST['subject'].lower()
    language = request.POST.get('language', 'slovak')

    questions, used_options = get_general_quiz_data(mode, start, request.user, subject)

    if isinstance(questions, dict) and "error" in questions.keys():
        messages.error(request, questions["error"])
        return redirect("/lfuk")

    repeat_quiz = RepeatQuiz.objects.get(name=subject, user=request.user, quiz_type="GENERAL")

    return render(request, "quiz.html", {
            "quiz_type": "general",
            "mode": mode,
            "subject": subject,
            "start": start,
            "language": language,
            "voice_recognition": voice_recognition,
            "subject_display_name": subjects[subject],
            "language_display_name": languages[language][1],
            "questions": json.dumps(questions),
            "used_options": json.dumps(used_options),
            "negative_marking": 1,
            "repeat_quiz_slug": repeat_quiz.slug,
            "parent_slug": "",
        }
    )

def loginStatusView(request):
    """
    Get user's authentication status
    """
    return JsonResponse({ "logged_in": request.user.is_authenticated })

@login_required
def update_repeat_quiz_name(request):
    """
    Create and save user's repeat quiz
    """

    data = json.loads(request.body.decode("utf-8"))
    quiz = RepeatQuiz.objects.filter(slug=data["slug"], user=request.user)

    if quiz.exists():
        quiz = quiz.first()
        saved_quiz = None

        if quiz.parent_slug:
            sq = SavedQuiz.objects.filter(slug=quiz.parent_slug, user=request.user)

            if sq.exists():
                saved_quiz = sq.first()
                
        if 0 < len(data["name"]) < 10:
            if saved_quiz and not SavedQuiz.objects.filter(name=data["name"], user=request.user, quiz_type=saved_quiz.quiz_type).exists():
                saved_quiz.name = data["name"]
                saved_quiz.save()
                quiz.name = data["name"]
                quiz.save()
            elif not RepeatQuiz.objects.filter(name=data["name"], user=request.user).exists():
                saved_quiz.name = data["name"]
                saved_quiz.save()
                quiz.name = data["name"]
                quiz.save()
            else:
                return JsonResponse({
                "status": "fail",
                    "data": {
                        "message": "Quiz name should be unique."
                    }
                })
        else:
            return JsonResponse({
                "status": "fail",
                "data": {
                    "message": "Quiz name should have atleast 1 character and at most 10 characters."
                }
            })

    return JsonResponse({
        "status": "success",
        "data": {
            "message": "Quiz name updated successfully!"
        }
    })

@login_required
def update_saved_quiz_name(request):
    """
    Create and save user's saved quiz
    """
    data = json.loads(request.body.decode("utf-8"))
    quiz = SavedQuiz.objects.filter(slug=data["slug"], user=request.user)

    if quiz.exists():
        quiz = quiz.first()

        if 0 < len(data["name"]) < 10 and not SavedQuiz.objects.filter(name=data["name"], user=request.user, quiz_type=quiz.quiz_type).exists():
            repeat_quiz = RepeatQuiz.objects.filter(parent_slug=quiz.slug)
            quiz.name = data["name"]
            quiz.save()

            if repeat_quiz.exists():
                repeat_quiz = repeat_quiz.first()
                repeat_quiz.name = data["name"]
                repeat_quiz.save()
        else:
            return JsonResponse({
                "status": "fail",
                "data": {
                    "message": "Quiz name should have atleast 1 character and at most 10 characters."
                }
            })

    return JsonResponse({
        "status": "success",
        "data": {
            "message": "Quiz name updated successfully!"
        }
    })

def userSubscription(request):
    """
    Get user subscription details
    """
    response = "undefined"

    if request.user.is_authenticated:
        if request.user.subscription.subscription.is_premium():
            response = "premium"
        elif request.user.subscription.subscription.is_free():
            response = "free"

    return JsonResponse({ "subscription": response })

@login_required
def repeat_quiz_save_options(request):
    """
    Save user-selected option to database
    """
    print(request.user.subscription.subscription)

    if not request.user.subscription.subscription.is_premium():
        return JsonResponse({
            "status": "fail",
            "data": {
                "message": "Feature reserved to premium accounts only!"
            }
        })

    question = json.loads(request.body.decode("utf-8"))["question"]
    quiz_data = json.loads(request.body.decode("utf-8"))["quizDetails"]

    print("QUIZ DATA:", quiz_data)
    print("QUESTION DATA:", question)
    
    # Validating repeat quiz
    quiz = RepeatQuiz.objects.filter(slug=quiz_data["repeat_quiz_slug"], user=request.user)

    if quiz.exists():
        quiz = quiz.first()
    else:
        return JsonResponse({
            "status": "fail",
            "data": {
                "message": "Repeat quiz doesn't exist."
            }
        })

    # Saving the question and option to the database
    # Repeat question
    repeat_question = RepeatQuizQuestion.objects.filter(question = question["questionNumber"], repeat_quiz=quiz)

    if repeat_question.exists():
        repeat_question = repeat_question.first()
    else:
        repeat_question = RepeatQuizQuestion.objects.create(
            repeat_quiz = quiz,
            question=question["questionNumber"],
            question_text=question["questionText"]
        )

    # Repeat option
    option = question["option"].replace(".", "")
    repeat_option = RepeatQuizOption.objects.filter(repeat_quiz_question=repeat_question, option=option)

    if not repeat_option.exists():    
        RepeatQuizOption.objects.create(
            repeat_quiz_question = repeat_question,
            option=option,
            option_text=question["optionText"],
            key=question["key"]
        )

    # Success response
    return JsonResponse({
        "status": "success",
        "data": {
            "message": "Selected option saved successfully!"
        }
    })

@login_required
def repeat_quiz_delete_options(request):
    """
    Delete question and option from the database
    """
    if not request.user.subscription.subscription.is_premium():
        return JsonResponse({
            "status": "fail",
            "data": {
                "message": "Feature reserved to premium accounts only!"
            }
        })

    question = json.loads(request.body.decode("utf-8"))["question"]
    quiz_data = json.loads(request.body.decode("utf-8"))["quizDetails"]

    print("QUIZ DATA:", quiz_data)
    print("QUESTION DATA:", question)
    
    # Validating repeat quiz
    quiz = RepeatQuiz.objects.filter(slug=quiz_data["repeat_quiz_slug"], user=request.user)

    if quiz.exists():
        quiz = quiz.first()
    else:
        return JsonResponse({
            "status": "fail",
            "data": {
                "message": "Repeat quiz doesn't exist."
            }
        })

    # Deleting the question and option from the database
    # Repeat question
    repeat_question = RepeatQuizQuestion.objects.filter(question = question["questionNumber"], repeat_quiz=quiz)

    if repeat_question.exists():
        repeat_question = repeat_question.first()
    
    # Repeat option
    option = question["option"].replace(".", "")
    repeat_option = RepeatQuizOption.objects.filter(repeat_quiz_question=repeat_question, option=option)

    if repeat_option.exists():    
        repeat_option.first().delete()

    if repeat_question.get_options_count() == 0:
        repeat_question.delete()

    # Success response
    return JsonResponse({
        "status": "success",
        "data": {
            "message": "Option deleted successfully!"
        }
    })

@login_required
def delete_repeat_quiz_questions(request, slug):
    if (not request.user.subscription.subscription.is_premium()) and (mode in [3, 4]):
        return return_to_previous_url(request)

    quiz = RepeatQuiz.objects.filter(slug=slug, user=request.user)

    if quiz.exists():
        quiz = quiz.first()
        quiz.get_questions().delete()
    
    return return_to_previous_url(request)

@login_required
def delete_saved_quiz(request, slug):
    quiz = SavedQuiz.objects.filter(slug=slug, user=request.user)

    if quiz.exists():
        quiz = quiz.first()

        # Deleting the associated repeat quiz
        repeat_quiz = RepeatQuiz.objects.filter(parent_slug=quiz.slug)

        if repeat_quiz.exists():
            repeat_quiz.first().delete()

        quiz.delete()
    
    return redirect("/exam-creator")

@login_required
def repeat_quiz(request, slug, mode):
    if (not request.user.subscription.subscription.is_premium()) and (mode in [3, 4]):
        return return_to_previous_url(request)

    # Validating quiz mode
    if not (mode in [3, 4]):
        messages.error(request, "Invalid mode value provided.")
        return return_to_previous_url(request)

    # Validating repeat quiz
    quiz = RepeatQuiz.objects.filter(slug=slug, user=request.user)
    
    if quiz.exists():
        quiz = quiz.first()
    else:
        messages.error(request, "Quiz doesn't exist.")
        return redirect("/")

    start = 0

    if mode == 4:
        start = request.POST["start"]
        start = int(start)

    questions, used_options = get_repeat_quiz_data(quiz, start)

    # Validating saved quiz
    if quiz.parent_slug and quiz.quiz_type == "SAVED":
        saved_quiz = SavedQuiz.objects.filter(slug = quiz.parent_slug)

        if saved_quiz.exists():
            saved_quiz = saved_quiz.first()

            return render(request, "quiz.html", {
                "quiz_type": "repeat",
                "repeat_quiz_slug": quiz.slug,
                "parent_slug": quiz.parent_slug,
                "mode": mode,
                "subject": quiz.name,
                "start": 1,
                "language": saved_quiz.language,
                "voice_recognition": saved_quiz.voice_recognition,
                "negative_marking": "1" if saved_quiz.negative_marking else "0",
                "subject_display_name": subjects[saved_quiz.name] if saved_quiz.name in subjects.keys() else saved_quiz.name,
                "language_display_name": languages[saved_quiz.language][1],
                "questions": json.dumps(questions),
                "used_options": json.dumps(used_options)
            })
    
    return render(request, "quiz.html", {
        "quiz_type": "repeat",
        "repeat_quiz_slug": quiz.slug,
        "parent_slug": "",
        "mode": mode,
        "subject": quiz.name,
        "start": 1,
        "language": request.POST["language"],
        "voice_recognition": request.POST["voice_recognition"] == "1",
        "negative_marking": "1",
        "subject_display_name": subjects[quiz.name] if quiz.name in subjects.keys() else quiz.name,
        "language_display_name": languages[request.POST["language"]][1],
        "questions": json.dumps(questions),
        "used_options": json.dumps(used_options)
    })

@login_required
def saved_quiz(request, slug, mode):
    """
    View for saved quiz
    """
    if request.method == "POST":
        quiz = SavedQuiz.objects.filter(slug=slug, user=request.user)
        print("QUIZ:", quiz)

        if quiz.exists():
            quiz = quiz.first()
        else:
            return redirect("/exam-creator")

        repeat_quiz = RepeatQuiz.objects.filter(parent_slug=quiz.slug)

        if repeat_quiz.exists():
            repeat_quiz = repeat_quiz.first()
        else:
            messages.error(request, "No associated repeat quiz found.")
            return redirect("/exam-creator")

        start = 1

        if mode in [2, 4]:
            if "start" not in request.POST.keys() or request.POST["start"].strip() in [None, ""]:
                messages.error(request, f"Incorrect start value provided for Mode {mode}.")
                return redirect("/exam-creator")

            if not request.POST["start"].isnumeric():
                messages.error(request, f"Start value should be a positive integer for Mode {mode}.")
                return redirect("/exam-creator")

            start = int(request.POST["start"].strip())

        questions, used_options = get_saved_quiz_data(quiz, start, mode)

        return render(request, "quiz.html", {
            "quiz_type": "saved",
            "saved_quiz_slug": quiz.slug,
            "repeat_quiz_slug": repeat_quiz.slug,
            "mode": mode,
            "subject": quiz.name,
            "start": start,
            "language": quiz.language,
            "voice_recognition": quiz.voice_recognition,
            "negative_marking": "1" if quiz.negative_marking else "0",
            "subject_display_name": subjects[quiz.name] if quiz.name in subjects.keys() else quiz.name,
            "language_display_name": languages[quiz.language][1],
            "questions": json.dumps(questions),
            "used_options": json.dumps(used_options)
        })

    return redirect("/exam-creator")