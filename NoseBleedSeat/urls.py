from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name='home'),
    path("about/", views.about, name='about'),
    path('update-league-leaders/', views.update_league_leaders, name='update_league_leaders'),
    path('autocomplete/player/', views.search_autocomplete, name='search_autocomplete'),
    path('show-career-awards-player1/<str:player1_name>/<str:player1_id>', views.show_career_awards_player1, name='show_career_awards_player1'),
    path('show-career-awards-player2/<str:player2_name>/<str:player2_id>', views.show_career_awards_player2, name='show_career_awards_player2'),
    path('compare-graph/<str:player1_name>/<int:player1_id>/<str:player2_name>/<int:player2_id>/', views.home_compare_graph, name='home_compare_graph'),
    path('htmx/swap-player1/', views.htmx_swap_player1, name='htmx_swap_player1'),
    path('htmx/swap-player2/', views.htmx_swap_player2, name='htmx_swap_player2'),
]



