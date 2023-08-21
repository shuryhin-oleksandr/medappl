import secrets
from tabnanny import verbose
from django.db import models
from email.policy import default
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from myproject.settings import AUTH_USER_MODEL as User
from quiz.models import RepeatQuiz

class User(AbstractUser):
    pass

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_confirmed = models.BooleanField(default=False)
    reset_password = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'auth'

def uniqueSubscriptionSlug():
    return secrets.token_hex(10)

class Subscription(models.Model):
    name = models.CharField(max_length = 25)
    slug = models.SlugField(max_length = 20, unique = True, default = uniqueSubscriptionSlug)
    dateCreated = models.DateTimeField(auto_now_add = True)
    lastUpdated = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name

    def is_free(self):
        return self.name == "free"

    def is_premium(self):
        return self.name == "premium"

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = "subscription")
    subscription = models.ForeignKey(Subscription, on_delete = models.SET_NULL, null = True, related_name = "users")
    dateCreated = models.DateTimeField(auto_now_add = True)
    lastUpdated = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = "UserSubscription"
        verbose_name_plural = "UserSubscriptions"

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

        # Creating repeat quizzes for the basic/general quizzes
        RepeatQuiz.objects.create(
            name="biology",
            user=instance
        )
        RepeatQuiz.objects.create(
            name="chemistry",
            user=instance
        )

    instance.profile.save()