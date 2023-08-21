from django.contrib.auth.signals import user_logged_in
from .models import User
from django.dispatch import receiver

from django.contrib.sessions.models import Session


@receiver(user_logged_in,sender=User)
def show_login(sender, request, **kwargs):
    all_sessions = Session.objects.all()
    print("Na váš účet bolo prihlásené ďaĺšie zariadenie.",request.user.id, request.session.session_key)
    # Delete previous sessions
    for session in all_sessions:
        try:
            session_dict = session.get_decoded()
            if str(session_dict['_auth_user_id']) == str(request.user.id):
                session.delete()
        except:
            continue




# user_logged_in.connect(show_login)

# TODO: Set login redirect
# TODO: Make front-end log out user