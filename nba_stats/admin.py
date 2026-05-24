from django.contrib import admin
from .models import Player, PlayerBio, CareerAwards, LeagueLeaders, PlayerStats, CareerStat, SeasonStat, SeasonHigh, SeasonRanking

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    search_fields = ['full_name', 'first_name', 'last_name']
    list_display = ['full_name', 'status', 'team']
    list_filter = ['status']
@admin.register(PlayerBio)
class PlayerBioAdmin(admin.ModelAdmin):
    search_fields = ['player__full_name', 'player__first_name', 'player__last_name']
    list_display = ['player', 'position', 'school', 'country']
admin.site.register(CareerAwards)
admin.site.register(LeagueLeaders)
admin.site.register(PlayerStats)
admin.site.register(CareerStat)
admin.site.register(SeasonStat)
admin.site.register(SeasonHigh)
admin.site.register(SeasonRanking)
