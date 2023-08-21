from symbol import subscript
from workers.models import Worker
from clients.models import Client
from contract.models import Contract
from user.models import HandyUser as User
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login
from django.views.generic import DetailView,ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.forms import UserCreationForm
from users.models import Subscription, UserSubscription
from django.contrib.auth.decorators import login_required


class HandyUserCreationForm(UserCreationForm):
	class Meta:
		model = User
		fields = UserCreationForm.Meta.fields + ('is_client','email')
    
def assignStatus(user,is_client):
	if is_client == 'on':
		return Client(user=user)
	else:
		return Worker(user=user)

def RegisterView(request):
	if request.method == "GET":
		form = HandyUserCreationForm()
	elif request.method == "POST":
		form = HandyUserCreationForm(request.POST)

		if form.is_valid():
			form.save()
			'''Obtain proper user from db and create either Client or Worker model for it
				depending on the 'is_client' value
			'''
			user = User.objects.get(username=request.POST['username'])
			FREE_SUBSCRIPTION = Subscription.objects.get(name="free")
			UserSubscription.objects.create(
				user = user,
				subscription = FREE_SUBSCRIPTION
			)
			is_client = request.POST['is_client']
			person = assignStatus(user,is_client)
			person.save()

			username = request.POST['username']
			password = request.POST['password1']
			auth_user = authenticate(request,username=username,password=password)
			
			if auth_user is not None:
				login(request,auth_user)

			return redirect("/user/")

	return render(request,"registration/register.html",{"form":form})

@method_decorator(login_required(),name="dispatch")
class ProfileView(DetailView):
	template_name = "user/index.html"
	context_object_name = "person"

	def get_object(self):
		user = self.request.user
		if user.is_client:
			return Client.objects.get(user=user)
		else:
			return Worker.objects.get(user=user)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		if user.is_client:
			all_contracts = Contract.objects.filter(client__user=user).order_by("created_on")
			active_contracts = all_contracts.filter(work_status="AC")
			inactive_contracts = all_contracts.filter(work_status="NB")
			context['contracts'] = all_contracts
			context['active_contracts'] = active_contracts
			context['inactive_contracts'] = inactive_contracts
		return context