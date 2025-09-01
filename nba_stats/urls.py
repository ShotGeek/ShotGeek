from django.urls import path
from . import views

app_name = 'nba_stats'

urlpatterns = [

    path('player-comparison-search/', views.compare_players, name='compare_players'),
    path('update-player-awards/<str:player_name>/<str:player_id>', views.update_player_awards, name='update_player_awards'),
    path('update-player-bio/<str:player_name>/<str:player_id>', views.update_player_bio, name='update_player_bio'),
    path('graph-comparison/<str:player1_full_name>/<str:player1_id>/<str:player2_full_name>/<str:player2_id>/', views.show_graph, name='show_graph'),
    path('player-comparison-profiles/<str:player1_full_name>/<str:player1_id>/<str:player2_full_name>/<str:player2_id>/', views.compare_profiles, name='compare_profiles'),
    path('player-career-page/<str:player_full_name>/<str:player_id>/', views.player_details, name='player_details'),
    path('regular-season-totals/<str:player_full_name>/<str:player_id>/', views.regular_season, name='regular_season'),
    path('post-season-totals/<str:player_full_name>/<str:player_id>/', views.post_season, name='post_season'),
    path('regular-season-rankings/<str:player_full_name>/<str:player_id>/', views.regular_season_rankings,
         name='regular_season_rankings'),
    path('post-season-rankings/<str:player_full_name>/<str:player_id>/', views.post_season_rankings,
         name='post_season_rankings'),
    path('player-graph/<str:player_full_name>/<str:player_id>/<str:category>/', views.player_graph,
         name='player_graph'),
     path('player-game-log/<str:player_full_name>/<str:player_id>/<str:season>/<str:season_type>/', views.player_game_log, name='player_game_log'),
     path('player-shot-chart/<str:player_full_name>/<str:player_id>/<str:season>/<str:season_type>/<str:context_measure>/<str:team_id>/', views.player_shot_chart, name='player_shot_chart'),
]
