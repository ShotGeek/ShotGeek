from django.shortcuts import render

from nba_stats.forms import PlayerSearchForm
from .functions import get_team, get_team_history, retired_players, get_team_rankings, get_team_roster
import time


def team_page(request, team_id):
    # team logo and other information
    team_info = get_team(team_id)
    team_name = team_info[5]

    # championships and current relevant info
    team_history = get_team_history(team_id)
    current_info = team_history[0]
    head_coach = current_info['HEADCOACH']
    arena = current_info['ARENA']

    championships = team_history[1]

    # retired players
    retired = retired_players(team_id, team_name)

    # team ranks
    team_ranks = get_team_rankings(team_id)
    time.sleep(6)

    # team_roster
    roster = get_team_roster(team_id)

    # search form
    player_form = PlayerSearchForm()

    context = {
        'player_form': player_form,
        'team_info': team_info,
        'team_id': team_id,
        'head_coach': head_coach,
        'arena': arena,
        'championships': championships,
        'retired': retired,
        'team_ranks': team_ranks,
        'roster': roster
    }

    return render(request, 'nba_teams/team_page.html', context=context)