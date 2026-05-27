from django.shortcuts import render, redirect
from django.contrib import messages
from nba_api.stats.static import players
from nba_stats.forms import PlayerSearchForm, StatsCompForm
from nba_stats.models import Player, PlayerBio, PlayerStats, LeagueLeaders, TEAM_COLOURS, SeasonStat
from nba_stats.functions import create_proxy_url
from .forms import PlayerOneForm, PlayerTwoForm
from nba_teams.models import NBATeam
from django.db.models import Q
from django.utils import timezone
import threading
from nba_api.stats.static import players as static_players


# Cache the complete static player list at module import time so
# subsequent autocomplete requests filter the in-memory list instead
# of calling the API on every keystroke.
try:
    ALL_PLAYERS = players.get_players() or []
except Exception:
    ALL_PLAYERS = []
import os
import json
from dotenv import load_dotenv
from .functions import (
    get_word_of_the_day,
    get_player_awards,
    leagueleaders,
    save_player_bio,
)

# Load environment variables from .env file
load_dotenv()

_STAT_FIELD_MAP = {
    'PPG':     ('pts',     False),
    'RPG':     ('reb',     False),
    'DREB':    ('dreb',    False),
    'APG':     ('ast',     False),
    'BLKPG':   ('blk',     False),
    'STLPG':   ('stl',     False),
    'FGA':     ('fga',     False),
    'FG3A':    ('fg3a',    False),
    'FG3M':    ('fg3m',    False),
    'FTA':     ('fta',     False),
    'FTM':     ('ftm',     False),
    'OREB':    ('oreb',    False),
    'FG_PCT':  ('fg_pct',  True),
    'FG3_PCT': ('fg3_pct', True),
    'FT_PCT':  ('ft_pct',  True),
}


def _build_archive_graph(player1_id, player1_name, player2_id, player2_name, stat_category):
    """Query SeasonStat and return Chart.js-ready data grouped by season."""
    if stat_category not in _STAT_FIELD_MAP:
        return None

    field, is_pct = _STAT_FIELD_MAP[stat_category]
    percent_categories = {'FG_PCT', 'FG3_PCT', 'FT_PCT'}

    def _season_vals(pid):
        qs = (
            SeasonStat.objects
            .filter(player__player_id=pid, season_type='Regular')
            .order_by('season_id')
            .values('season_id', field, 'games_played')
        )
        result = {}
        for row in qs:
            gp = row['games_played'] or 1
            val = row[field] or 0
            result[row['season_id']] = round(val, 3) if is_pct else round(val / gp, 1)
        return result

    p1_by_season = _season_vals(int(player1_id))
    p2_by_season = _season_vals(int(player2_id))

    if not p1_by_season and not p2_by_season:
        return None

    p1_vals = list(p1_by_season.values())
    p2_vals = list(p2_by_season.values())
    num_years = max(len(p1_vals), len(p2_vals))

    # Pad the shorter career with 0s so both datasets have the same length
    p1_vals += [0] * (num_years - len(p1_vals))
    p2_vals += [0] * (num_years - len(p2_vals))

    # Convert stored 0.0-1.0 fractions to percentages for the graph
    if stat_category in percent_categories:
        p1_vals = [round(v * 100, 1) for v in p1_vals]
        p2_vals = [round(v * 100, 1) for v in p2_vals]

    labels = [f"Year {i + 1}" for i in range(num_years)]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": player1_name,
                "data": p1_vals,
                "borderColor": "#00284D",
                "backgroundColor": "rgba(0,40,77,0.50)",
                "fill": True,
            },
            {
                "label": player2_name,
                "data": p2_vals,
                "borderColor": "#F85D2B",
                "backgroundColor": "rgba(248,93,43,0.50)",
                "fill": True,
            },
        ],
    }


def home_compare_graph(request, player1_name, player1_id, player2_name, player2_id):
    player1_name = request.session.get('player1', player1_name)
    player1_match = static_players.find_players_by_full_name(player1_name.title())
    player1_id = player1_match[0]['id'] if player1_match else player1_id

    player2_name = request.session.get('player2', player2_name)
    player2_match = static_players.find_players_by_full_name(player2_name.title())
    player2_id = player2_match[0]['id'] if player2_match else player2_id
    
    stat = request.GET.get('stat', 'PPG')
    if stat.startswith('---'):
        stat = 'PPG'

    form = StatsCompForm(initial={'option': stat})
    title = form.get_graph_title(stat)

    graph_data = _build_archive_graph(player1_id, player1_name, player2_id, player2_name, stat)

    context = {
        'form': form,
        'graph_json': json.dumps(graph_data) if graph_data else 'null',
        'stat_label': title,
        'selected_stat': stat,
        'player1_name': player1_name,
        'player1_id': player1_id,
        'player2_name': player2_name,
        'player2_id': player2_id,
    }
    return render(request, 'partials/home_compare_graph.html', context)


def _resolve_player(name):
    """Look up a player by full name, return data dict or None."""
    matches = static_players.find_players_by_full_name(name)
    if not matches:
        return None
    player = Player.objects.filter(player_id=matches[0]['id']).first()
    if not player:
        return None
    bio = PlayerBio.objects.filter(player=player).first()
    stats = PlayerStats.objects.filter(player=player).first()
    colour = TEAM_COLOURS.get(player.team_id, '#1d428a')
    return {'player': player, 'bio': bio, 'stats': stats, 'colour': colour}


def _normalize_stats(stats):
    if not stats:
        return [0, 0, 0, 0, 0]
    maxes = [35.0, 15.0, 12.0, 3.5, 3.0]
    vals = [stats.PTS, stats.REB, stats.AST, stats.BLK, stats.STL]
    return [round(min(v / m * 100, 100), 1) for v, m in zip(vals, maxes)]


def htmx_swap_player1(request):
    error = None
    if request.method == 'POST':
        form = PlayerOneForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['player1_name'].title()
            if _resolve_player(name):
                request.session['player1'] = name
                threading.Thread(target=save_player_bio, args=(name.lower(),), daemon=True).start()
            else:
                error = f"Player '{name}' not found."

    player1_name = request.session.get('player1', 'LeBron James')
    p1 = _resolve_player(player1_name)
    context = {
        'player1': p1['player'],
        'player1_bio': p1['bio'],
        'player1_stats': p1['stats'],
        'player1_colour': p1['colour'],
        'player1_stats_norm': _normalize_stats(p1['stats']),
        'player1_form': PlayerOneForm(),
        'player1_error': error,
    }
    return render(request, 'partials/player1_card.html', context)


def htmx_swap_player2(request):
    error = None
    if request.method == 'POST':
        form = PlayerTwoForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['player2_name'].title()
            if _resolve_player(name):
                request.session['player2'] = name
                threading.Thread(target=save_player_bio, args=(name.lower(),), daemon=True).start()
            else:
                error = f"Player '{name}' not found."

    player2_name = request.session.get('player2', 'Michael Jordan')
    p2 = _resolve_player(player2_name)
    context = {
        'player2': p2['player'],
        'player2_bio': p2['bio'],
        'player2_stats': p2['stats'],
        'player2_colour': p2['colour'],
        'player2_stats_norm': _normalize_stats(p2['stats']),
        'player2_form': PlayerTwoForm(),
        'player2_error': error,
    }
    return render(request, 'partials/player2_card.html', context)


def home(request):
    PLAYLIST_ID = os.getenv('PLAYLIST_ID')
    word_of_the_day = get_word_of_the_day()
    player_form = PlayerSearchForm()
    player1_form = PlayerOneForm()
    player2_form = PlayerTwoForm()

    # reset data
    request.session.pop('player_page_info', None)
    request.session.pop('player_info', None)
    request.session.pop('player_compare_info', None)

    # restore user session or default to Lebron and MJ if there's none
    player1_name = request.session.get('player1', 'LeBron James')
    player2_name = request.session.get('player2', 'Michael Jordan')

    p1 = _resolve_player(player1_name)
    if not p1:
        request.session.pop('player1', None)
        messages.error(request, f"Player '{player1_name}' not found. Please check the spelling.")
        return redirect('home')

    p2 = _resolve_player(player2_name)
    if not p2:
        request.session.pop('player2', None)
        messages.error(request, f"Player '{player2_name}' not found. Please check the spelling.")
        return redirect('home')

    if request.method == 'POST':
        player_form = PlayerSearchForm(request.POST)
        if player_form.is_valid():
            term = player_form.cleaned_data['player_name'].strip()
            team = NBATeam.objects.filter(
                Q(full_name__iexact=term) | Q(name__iexact=term) |
                Q(city__iexact=term) | Q(abbreviation__iexact=term)
            ).first()
            if team:
                return redirect('nba_teams:team_page', team_id=team.team_id)
            matches = static_players.find_players_by_full_name(term.title())
            if matches:
                return redirect('nba_stats:player_details',
                                player_full_name=matches[0]['full_name'],
                                player_id=matches[0]['id'])
            messages.error(request, f"Could not find '{term}'.")
            return redirect('home')

        player1_form = PlayerOneForm(request.POST)
        if player1_form.is_valid():
            request.session['player1'] = player1_form.cleaned_data['player1_name'].title()
            player1_name = player1_form.cleaned_data['player1_name'].lower()
            threading.Thread(target=save_player_bio, args=(player1_name,), daemon=True).start()
            return redirect('home')

        player2_form = PlayerTwoForm(request.POST)
        if player2_form.is_valid():
            request.session['player2'] = player2_form.cleaned_data['player2_name'].title()
            player2_name = player2_form.cleaned_data['player2_name'].lower()
            threading.Thread(target=save_player_bio, args=(player2_name,), daemon=True).start()
            return redirect('home')

    context = {
        'player_form': player_form,
        'player1_form': player1_form,
        'player2_form': player2_form,
        'player1': p1['player'],
        'player2': p2['player'],
        'player1_bio': p1['bio'],
        'player2_bio': p2['bio'],
        'player1_stats': p1['stats'],
        'player2_stats': p2['stats'],
        'player1_colour': p1['colour'],
        'player2_colour': p2['colour'],
        'player1_stats_norm': _normalize_stats(p1['stats']),
        'player2_stats_norm': _normalize_stats(p2['stats']),
        'PLAYLIST_ID': PLAYLIST_ID,
        'word_of_the_day': word_of_the_day,
    }
    return render(request, 'index.html', context=context)

def search_autocomplete(request):
    # Use cached player list when available to avoid repeated API calls.
    all_players = ALL_PLAYERS if ALL_PLAYERS else (players.get_players() or [])

    query = (
        request.GET.get('q') or
        request.GET.get('player1_name') or
        request.GET.get('player2_name') or
        request.GET.get('player_name') or ''
    ).strip()

    # Only search when user has typed at least 2 chars
    if len(query) >= 2:
        q = query.lower()
        # Prioritize players whose names start with the query, then those that contain it
        starts = [p for p in all_players if p['full_name'].lower().startswith(q)]
        contains = [p for p in all_players if q in p['full_name'].lower() and not p in starts]
        matches = (starts + contains)[:15]
    else:
        matches = []

    context = {
        'players': matches,
        'count': len(all_players)
    }
    return render(request, 'partials/player_auto_complete.html', context=context)

def about(request):
    PLAYLIST_ID = os.getenv('PLAYLIST_ID')
    player_form = PlayerSearchForm()
    context = {
        'player_form': player_form,
        'PLAYLIST_ID': PLAYLIST_ID

    }
    return render(request, "about.html", context=context)

# htmx linked function for show career awards
def show_career_awards_player1(request, player1_name, player1_id):
    player1_awards = get_player_awards(player_name=player1_name, player_id=player1_id)

    context = {
        "player1_awards": player1_awards,
        "player_name": player1_name
    }

    return render(request, "partials/career_awards_player1.html", context=context)

# htmx linked function for show career awards
def show_career_awards_player2(request, player2_name, player2_id):
    player2_awards = get_player_awards(player_name=player2_name, player_id=player2_id)

    context = {
        "player2_awards": player2_awards,
        "player_name": player2_name
    }

    return render(request, "partials/career_awards_player2.html", context=context)

# htmx linked function for updating league leaders section
def update_league_leaders(request):
    proxy_url = create_proxy_url

    stats = ["PTS", "BLK", "REB", "AST", "STL", "FGM", "FG3M", "FTM", "EFF", "AST_TOV", "STL_TOV"]
    stats_map = {
        'PTS': 'Points',
        'BLK': 'Blocks',
        'REB': 'Rebounds',
        'AST': 'Assists',
        'STL': 'Steals',
        'FGM': 'Field Goal Makes',
        'FG3M': '3 Point Field Goal Makes',
        'FTM': 'Free Throw Makes',
        'EFF': 'Individual Player Efficiency',
        'AST_TOV': 'Assists To Turnover Ratio',
        'STL_TOV': 'Steals To Turnover Ratio'
    }

    # Placeholder data if the API returns no data
    placeholder_data = {
        "Blocks": ["Victor Wembanyama", 254, "https://cdn.nba.com/headshots/nba/latest/1040x760/1641705.png", "#c4ced4",
                   1641705],
        "Points": ["Luka Doncic", 2370, "https://cdn.nba.com/headshots/nba/latest/1040x760/1629029.png", "#00538c",
                   1629029],
        "Steals": ["De'Aaron Fox", 150, "https://cdn.nba.com/headshots/nba/latest/1040x760/1628368.png", "#5a2d81",
                   1628368],
        "Assists": ["Tyrese Haliburton", 752, "https://cdn.nba.com/headshots/nba/latest/1040x760/1630169.png",
                    "#002d62", 1630169],
        "Rebounds": ["Domantas Sabonis", 1120, "https://cdn.nba.com/headshots/nba/latest/1040x760/1627734.png",
                     "#5a2d81", 1627734],
        "Field Goal Makes": ["Giannis Antetokounmpo", 837,
                             "https://cdn.nba.com/headshots/nba/latest/1040x760/203507.png", "#00471b", 203507],
        "Free Throw Makes": ["Shai Gilgeous-Alexander", 567,
                             "https://cdn.nba.com/headshots/nba/latest/1040x760/1628983.png", "#007ac1", 1628983],
        "3 Point Field Goal Makes": ["Stephen Curry", 357,
                                     "https://cdn.nba.com/headshots/nba/latest/1040x760/201939.png", "#ffc72c", 201939],
        "Steals To Turnover Ratio": ["Matisse Thybulle", 2.83,
                                     "https://cdn.nba.com/headshots/nba/latest/1040x760/1629680.png", "#e03a3e",
                                     1629680],
        "Assists To Turnover Ratio": ["Tyus Jones", 7.35,
                                      "https://cdn.nba.com/headshots/nba/latest/1040x760/1626145.png", "#e56020",
                                      1626145],
        "Individual Player Efficiency": ["Nikola Jokic", 3039,
                                         "https://cdn.nba.com/headshots/nba/latest/1040x760/203999.png", "#1d428a",
                                         203999]
    }

    # Initialize dictionary to hold the stat leaders
    stat_leaders = {}

    today = timezone.now().date()
    league_leaders_data = LeagueLeaders.objects.first()

    if league_leaders_data.date == today:
        stat_leaders = league_leaders_data.leaders

    else:


        # Get the league leaders data from the external API
        for category in stats:

            # prodcution with proxy
            if proxy_url:
                leaders = leagueleaders.LeagueLeaders(stat_category_abbreviation=category, proxy=proxy_url)
            # development without proxy
            else:
                leaders = leagueleaders.LeagueLeaders(stat_category_abbreviation=category)

                
            leaders_info = leaders.get_dict()

            # Extract the relevant data from the response
            leaders_list = leaders_info['resultSet']['headers']
            stat_index = leaders_list.index(category)  # checking the index for each stat category

            # check if there is any player data (data might be reset before a new season)
            if len(leaders_info['resultSet']['rowSet']) == 0:
                stat_leaders = placeholder_data

            else:
                # get new data
                # Player name and headshot
                # contains all the player info, will be empty if there's no data
                player_name = leaders_info['resultSet']['rowSet'][0][2]

                player_id = leaders_info['resultSet']['rowSet'][0][0]

                # Get or create player headshot
                player_headshot = PlayerHeadShot.objects.filter(player_name=player_name).first()

                if not player_headshot:
                    player_headshot = get_player_image(player_id)
                    player_headshot_instance = PlayerHeadShot.objects.create(
                        player_id=player_id,
                        player_name=player_name,
                        player_image_url=player_headshot[0] if player_headshot else "https://static.vecteezy.com/system/resources/thumbnails/004/511/281/small_2x/default-avatar-photo-placeholder-profile-picture-vector.jpg",
                        team_id=player_headshot[1] if player_headshot else 0,
                        background_colour=None  # Will be dynamically set later
                    )
                    player_headshot_instance.save()

                    player_headshot = PlayerHeadShot.objects.filter(player_id=player_id).first()

                player_image = player_headshot.player_image_url
                team_colour = player_headshot.background_colour

                # Stat value
                stat_value = leaders_info['resultSet']['rowSet'][0][stat_index]

                category_name = stats_map[category]
                stat_leaders[category_name] = [player_name, stat_value, player_image, team_colour, player_id]

                league_leaders_data.leaders = stat_leaders


    context = {
        'stat_leaders': stat_leaders
    }

    return render(request, 'partials/league_leaders.html', context=context)
