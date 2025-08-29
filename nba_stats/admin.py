from django.contrib import admin
from .models import PlayerHeadShot, PlayerBio, CareerAwards, LeagueLeaders

# Register your models here.
admin.site.register(PlayerHeadShot)
admin.site.register(PlayerBio)
admin.site.register(CareerAwards)
admin.site.register(LeagueLeaders)
