from django.contrib import admin
from .models import EasternConferenceTeams, WesternConferenceTeams, RetiredPlayers

# Register your models here.
admin.site.register(EasternConferenceTeams)
admin.site.register(WesternConferenceTeams)
admin.site.register(RetiredPlayers)
