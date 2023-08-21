from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text

from myproject.decorators import check_recaptcha, unauthenticated_required
from myproject.tokens import password_reset_token
from myproject.settings import config
from myproject.forms import UserPasswordResetForm

from django.contrib.auth import get_user_model, update_session_auth_hash
User = get_user_model()


@check_recaptcha
@require_http_methods(["GET", "POST"])
@unauthenticated_required(home_url='/', redirect_field_name='')
def reset(request, uidb64, token):

    if request.method == 'POST':
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            messages.add_message(request, messages.WARNING, str(e))
            user = None

        if user is not None and password_reset_token.check_token(user, token):
            form = UserPasswordResetForm(user=user, data=request.POST)
            if form.is_valid() and request.recaptcha_is_valid:
                form.save()
                update_session_auth_hash(request, form.user)

                user.is_active = True
                user.profile.reset_password = False
                user.save()
                messages.add_message(request, messages.SUCCESS, 'Reset hesla úspešný.')
                return redirect('/')
            else:
                context = {
                    'form': form,
                    'uid': uidb64,
                    'token': token
                }
                messages.add_message(request, messages.WARNING, 'Password could not be reset.')
                return render(request, 'registration/password_reset_conf.html', context)
        else:
            messages.add_message(request, messages.WARNING, 'Password reset link is invalid.')
            messages.add_message(request, messages.WARNING, 'Please request a new password reset.')

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        messages.add_message(request, messages.WARNING, str(e))
        user = None

    if user is not None and password_reset_token.check_token(user, token):
        context = {
            'form': UserPasswordResetForm(user),
            'uid': uidb64,
            'token': token
        }
        return render(request, 'registration/password_reset_conf.html', context)
    else:
        messages.add_message(request, messages.WARNING, 'Password reset link is invalid.')
        messages.add_message(request, messages.WARNING, 'Please request a new password reset.')

    return redirect('/')

