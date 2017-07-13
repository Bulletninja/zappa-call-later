from django.contrib import admin
from .models import CallLater


class CallLaterAdmin(admin.ModelAdmin):
    pass

admin.site.register(CallLater, CallLaterAdmin)

