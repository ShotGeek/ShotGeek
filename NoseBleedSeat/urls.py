"""NoseBleedSeat URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from NoseBleedSeat import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name='home'),
    path("about/", views.about, name='about'),
    path('update-league-leaders/', views.update_league_leaders, name='update_league_leaders'),
    path('show-career-awards-player1/<str:player1_name>/<str:player1_id>', views.show_career_awards_player1, name='show_career_awards_player1'),
    path('show-career-awards-player2/<str:player2_name>/<str:player2_id>', views.show_career_awards_player2, name='show_career_awards_player2'),
    path("stats/", include('nba_stats.urls')),
    path("nba-news/", include('nba_news.urls')),
    path("nba-today/", include('nba_today.urls')),
    path("nba-teams/", include('nba_teams.urls')),
]
