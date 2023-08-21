from secrets import token_hex
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, pre_save, post_delete

to_be_deleted_files = []

def generateSlug(length = 16):
    return token_hex(length)

def saved_quizzes_save_location(instance, filename):
    return '/'.join(['user-data', instance.user.username, "saved-quizzes", instance.slug, filename])

class SavedQuiz(models.Model):
    TYPE_CHOICES = (
        ("GENERAL", "General Quiz"),
        ("CUSTOM", "Custom Quiz"),
    )

    name = models.CharField(max_length=10)
    quiz_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="GENERAL")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="saved_quizzes")

    voice_recognition = models.BooleanField(default=True)
    negative_marking = models.BooleanField(default=True)
    language = models.CharField(max_length=25)

    number_of_questions = models.IntegerField()
    number_of_options_per_question = models.IntegerField()

    slug = models.SlugField(max_length=32, unique=True, default=generateSlug)

    questions = models.FileField(blank=True, upload_to=saved_quizzes_save_location)
    answers = models.FileField( upload_to=saved_quizzes_save_location)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} : {self.name}"

    def answers_filename(self):
        return self.answers.name.split("/")[-1]

    def questions_filename(self):
        return self.questions.name.split("/")[-1]

    class Meta:
        verbose_name = "SavedQuiz"
        verbose_name_plural = "SavedQuizzes"

class RepeatQuizManager(models.Manager):
    def get_quiz(self, type, name, parent_slug):
        quiz = super().get_queryset().filter(quiz_type=type, name=name, parent_slug=parent_slug)

        if quiz.exists():
            return quiz.first()

        return None

class RepeatQuiz(models.Model):
    TYPE_CHOICES = (
        ("GENERAL", "General Quiz"),
        ("SAVED", "Saved Quiz")
    )

    name = models.CharField(max_length=10)
    quiz_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="GENERAL")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="repeat_quizzes")

    slug = models.SlugField(max_length=32, unique=True, default=generateSlug)
    parent_slug = models.SlugField(max_length=32, blank=True, null=True, default=None)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = RepeatQuizManager()

    def __str__(self) -> str:
        return f"{self.user.username} : {self.name}"

    def number_of_questions(self):
        return self.questions.all().count()

    def get_questions(self):
        questions = self.questions.all()
        return questions

    def get_questions_sorted(self):
        questions = self.questions.all().order_by('question')
        questions = sorted(questions, key=lambda x : int(x.question) if x.question[-1] != '.' else int(x.question[:-1]))
        return questions

    def build_quiz_data(self, start = 0):
        questions = []
        used_options = set()
        quiz_questions = self.get_questions()

        for question in quiz_questions:
            number = question.question

            if number[-1] == '.':
                number = number[:-1]

            number = int(number)

            if number < start:
                continue

            question_object = {
                "id": question.slug,
                "question": question.question,
                "question_text": question.question_text,
                "options": []
            }

            for option in question.get_options():
                question_object["options"].append(option.to_json())
                used_options.add(option.option)

            questions.append(question_object)

        return questions, list(used_options)

    class Meta:
        verbose_name = "RepeatQuiz"
        verbose_name_plural = "RepeatQuizzes"

class RepeatQuizQuestion(models.Model):
    slug = models.SlugField(max_length=32, unique=True, default=generateSlug)
    repeat_quiz = models.ForeignKey(RepeatQuiz, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=10)
    question_text = models.TextField()
       
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.repeat_quiz.name} : {self.question}"

    def get_options(self):
        return self.options.all()

    def get_options_count(self):
        return self.options.all().count()

    class Meta:
        verbose_name = "RepeatQuizQuestion"
        verbose_name_plural = "RepeatQuizQuestions"

class RepeatQuizOption(models.Model):
    slug = models.SlugField(max_length=32, unique=True, default=generateSlug)
    repeat_quiz_question = models.ForeignKey(RepeatQuizQuestion, on_delete=models.CASCADE, related_name="options")
    option = models.CharField(max_length=10)
    option_text = models.TextField()
    key = models.CharField(max_length=1)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def get_questions(self):
        self.questions.all()

    def to_json(self):
        return {
            "option": self.option,
            "option_text": self.option_text,
            "key": self.key
        }

    def __str__(self) -> str:
        return f"{self.repeat_quiz_question.slug} : {self.option}"

    class Meta:
        verbose_name = "RepeatQuizOption"
        verbose_name_plural = "RepeatQuizOptions"
        ordering = ["option"]

@receiver(post_delete, sender=SavedQuiz)
def delete_saved_quiz_data_files(sender, instance, *args, **kwargs):
    if instance.questions:
        try:
            instance.questions.delete(save=False)
        except Exception as e:
            to_be_deleted_files.append(instance.questions.path)

    if instance.answers:
        try:
            instance.answers.delete(save=False)
        except Exception as e:
            to_be_deleted_files.append(instance.answers.path)