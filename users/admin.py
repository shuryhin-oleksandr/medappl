from django.contrib import admin
from .models import Subscription, UserSubscription

class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = ["name", "slug", "dateCreated", "lastUpdated"]
    list_filter = []  
    search_fields = ["name", "slug", "dateCreated", "lastUpdated"]

class UserSubscriptionAdmin(admin.ModelAdmin):
    model = UserSubscription
    list_display = ["getUserName", "getUserEmail", "getSubscriptionName", "dateCreated", "lastUpdated"]
    list_display_links = ["getUserName", "getUserEmail", "getSubscriptionName"]
    list_filter = ["subscription__name"]
    search_fields = ["subscription__name", "user__name", "user__email", "dateCreated", "lastUpdated"]

    def getUserName(self, us):
        return us.user.username

    getUserName.short_description = "User's Name"

    def getUserEmail(self, us):
        return us.user.email

    getUserEmail.short_description = "User's Email"

    def getSubscriptionName(self, us):
        return us.subscription.name

    getSubscriptionName.short_description = "Subscription"

admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)