from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text

from myproject.decorators import check_recaptcha, unauthenticated_required
from myproject.tokens import password_reset_token
from myproject.forms import UserForgotPasswordForm
from myproject.settings import config

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from django.contrib.auth import get_user_model
User = get_user_model()


@check_recaptcha
@require_http_methods(["GET", "POST"])
@unauthenticated_required(home_url='/', redirect_field_name='')
def password_reset(request):
    """User forgot password form view."""
    msg = ''
    if request.method == "POST":
        form = UserForgotPasswordForm(request.POST)
        if form.is_valid() and request.recaptcha_is_valid:
            email = request.POST.get('email')
            qs = User.objects.filter(email=email)
            site = get_current_site(request)

            if len(qs) > 0:
                user = qs[0]
                user.is_active = False  # User needs to be inactive for the reset password duration
                user.profile.reset_password = True
                user.save()

                message = render_to_string('registration/password_reset_mail.html', {
                    'user': user,
                    'protocol': 'http',
                    'domain': site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': password_reset_token.make_token(user),
                })

                message = Mail(
                    from_email='medicina.appl@gmail.com',
                    to_emails=email,
                    subject='Resetovanie hesla na medappl.com',
                    html_content=message)
                try:
                    sg = SendGridAPIClient(config['SENDGRID_API_KEY'])
                    response = sg.send(message)
                except Exception as e:
                    print(e)

            messages.add_message(request, messages.SUCCESS, 'Na email {0} bol poslaný odkaz na reset hesla.'.format(email))
            msg = 'Ak máme v databáze Váš email, bude Vám poslaný odkaz na resetovanie.'
        else:
            messages.add_message(request, messages.WARNING, 'Tento email nie je v našej databáze.')
            return render(request, 'registration/password_reset_req.html', {'form': form})

    return render(request, 'registration/password_reset_req.html', {'form': UserForgotPasswordForm, 'msg': msg})
