import json
from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import PlayerSearchForm, StatsDropdownForm, PlayerCompareForm, StatsCompForm, PlayerGraphForm
from NoseBleedSeat.functions import (
    get_player_bio, 
    fetch_player_data, 
    get_player_image,
    get_accolades,
)
from nba_stats.models import PlayerBio, CareerAwards
from .functions import (
    get_player_graph,
    player_regular_season,
    player_post_season,
    rankings_regular_season,
    rankings_post_season,
    get_graph,
    player_career_numbers
)
from nba_api.stats.static import players


def player_details(request, player_full_name, player_id):
    # session info will be from if the user clicks on either player1 or player2 on the home page
    player_info = request.session.get("player_info", None)

    if player_info:

        # save data
        player_headshot = player_info[0]

        player_bio = player_info[1]

    elif player_info is None:
        # Search for the player data
        player_headshot, player_bio, player_id = fetch_player_data(player_full_name, player_id)

        player_headshot = [player_headshot.player_image_url, player_headshot.background_colour]

        del player_bio['_state']

    # Get player career stats
    career_stats = player_career_numbers(player_id)
    player_stats = career_stats['CareerTotalsRegularSeason']

    for season_data in player_stats:

        # points per game
        if season_data['GP'] > 0 and season_data['PTS'] is not None:
            season_data['PPG'] = round(season_data['PTS'] / season_data['GP'], 2)
        else:
            season_data['PPG'] = 0  # To avoid division by zero in case GP is 0

        # assists per game
        if season_data['GP'] > 0 and season_data['AST'] is not None:
            season_data['APG'] = round(season_data['AST'] / season_data['GP'], 1)
        else:
            season_data['APG'] = 0

        # blocks per game
        if season_data['GP'] > 0 and season_data['BLK'] is not None:
            season_data['BLKPG'] = round(season_data['BLK'] / season_data['GP'], 1)
        else:
            season_data['BLKPG'] = 0

        # rebounds per game
        if season_data['GP'] > 0 and season_data['REB'] is not None:
            season_data['RPG'] = round(season_data['REB'] / season_data['GP'], 1)
        else:
            season_data['RPG'] = 0

        # steals per game
        if season_data['GP'] > 0 and season_data['STL'] is not None:
            season_data['STLPG'] = round(season_data['STL'] / season_data['GP'], 1)
        else:
            season_data['STLPG'] = 0

        # Certain players (specifically from before 1980) don't have a 3pt %
        if season_data['FG3_PCT'] is None:
            season_data['FG3_PCT'] = 0

    # get player awards
    #player_awards = get_player_awards(player_full_name, player_id)

    # save information in session for quicker access
    player_page_info = [player_headshot, player_bio, career_stats]
    request.session['player_page_info'] = player_page_info

    # Initialize forms
    player_form = PlayerSearchForm()
    form = StatsDropdownForm()
    graph_form = PlayerGraphForm()

    if request.method == 'POST':
        form = StatsDropdownForm(request.POST)
        if form.is_valid():
            stats_option = form.cleaned_data['option']

            # regular season numbers
            if stats_option == 'Reg. Season':
                return redirect('nba_stats:regular_season', player_id=player_id, player_full_name=player_full_name)

            elif stats_option == 'Post Season':
                return redirect('nba_stats:post_season', player_id=player_id, player_full_name=player_full_name)

            elif stats_option == 'Reg. Season Rankings':
                return redirect('nba_stats:regular_season_rankings', player_id=player_id,
                                player_full_name=player_full_name)

            elif stats_option == 'Post Season Rankings':
                return redirect('nba_stats:post_season_rankings', player_id=player_id,
                                player_full_name=player_full_name)

            else:
                return redirect('home')

        graph_form = PlayerGraphForm(request.POST)
        if graph_form.is_valid():
            career_category = graph_form.cleaned_data['career_category']
            stat_option = graph_form.cleaned_data['stat_option']

            title = graph_form.get_graph_title(stat_option)
            graph,stat = get_player_graph(player_id=player_id, player_name=player_full_name, career_stats=career_stats,
                                     stat_category=stat_option, career_category=career_category,
                                     title=title)
            # Append graph and stat to players info list and store in session for use in next view
            player_page_info.append(graph)
            player_page_info.append(stat)
            return redirect('nba_stats:player_graph', player_id=player_id, player_full_name=player_full_name,
                            category=stat_option)

    context = {'player_form': player_form,
               'player_headshot': player_headshot,
               'player_full_name': player_full_name,
               'player_stats': player_stats,
               'player_id': player_id,
               'form': form,
               'player_bio': player_bio,
               'graph_form': graph_form
               }

    return render(request, 'nba_stats/career_stats.html', context=context)


# regular season totals
def regular_season(request, player_full_name, player_id):
    # get session info containing player headshot, bio awards and career stats
    player_page_info = request.session.get("player_page_info", None)

    if player_page_info:
        player_headshot = player_page_info[0]
        player_bio = player_page_info[1]

        # get regular season stats
        career_stats = player_page_info[2]
        player_stats = career_stats['SeasonTotalsRegularSeason']

    else:
        # Get player headshot
        player_headshot = get_player_image(player_id)

        # Get players yearly numbers
        player_stats = player_regular_season(player_id)

        # get player bio
        player_bio = get_player_bio(player_full_name)

    for season_data in player_stats:

        # points per game
        if season_data['GP'] > 0 and season_data['PTS'] is not None:
            season_data['PPG'] = round(season_data['PTS'] / season_data['GP'], 2)
        else:
            season_data['PPG'] = 0  # To avoid division by zero in case GP is 0

        # assists per game
        if season_data['GP'] > 0 and season_data['AST'] is not None:
            season_data['APG'] = round(season_data['AST'] / season_data['GP'], 1)
        else:
            season_data['APG'] = 0

        # blocks per game
        if season_data['GP'] > 0 and season_data['BLK'] is not None:
            season_data['BLKPG'] = round(season_data['BLK'] / season_data['GP'], 1)
        else:
            season_data['BLKPG'] = 0

        # rebounds per game
        if season_data['GP'] > 0 and season_data['REB'] is not None:
            season_data['RPG'] = round(season_data['REB'] / season_data['GP'], 1)
        else:
            season_data['RPG'] = 0

        # steals per game
        if season_data['GP'] > 0 and season_data['STL'] is not None:
            season_data['STLPG'] = round(season_data['STL'] / season_data['GP'], 1)
        else:
            season_data['STLPG'] = 0

        # Certain players (specifically from before 1980) don't have a 3pt %
        if season_data['FG3_PCT'] is None:
            season_data['FG3_PCT'] = 0

    # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player_headshot': player_headshot,
               'player_full_name': player_full_name,
               'player_stats': player_stats,
               'player_id': player_id,
               'player_bio': player_bio,
               #'player_awards': player_awards
               }

    return render(request, 'nba_stats/regular_season.html', context=context)


# post season totals
def post_season(request, player_full_name, player_id):
    # get session info containing player headshot, bio awards and career stats
    player_page_info = request.session.get("player_page_info", None)

    if player_page_info:
        player_headshot = player_page_info[0]
        player_bio = player_page_info[1]

        # get regular season stats
        career_stats = player_page_info[2]
        player_stats = career_stats['SeasonTotalsPostSeason']

    else:
        # Get player headshot
        player_headshot = get_player_image(player_id, player_full_name)

        # Get players yearly numbers
        player_stats = player_post_season(player_id)

        # get player bio
        player_bio = get_player_bio(player_full_name)

    for season_data in player_stats:

        # points per game
        if season_data['GP'] > 0 and season_data['PTS'] is not None:
            season_data['PPG'] = round(season_data['PTS'] / season_data['GP'], 2)
        else:
            season_data['PPG'] = 0  # To avoid division by zero in case GP is 0

        # assists per game
        if season_data['GP'] > 0 and season_data['AST'] is not None:
            season_data['APG'] = round(season_data['AST'] / season_data['GP'], 1)
        else:
            season_data['APG'] = 0

        # blocks per game
        if season_data['GP'] > 0 and season_data['BLK'] is not None:
            season_data['BLKPG'] = round(season_data['BLK'] / season_data['GP'], 1)
        else:
            season_data['BLKPG'] = 0

        # rebounds per game
        if season_data['GP'] > 0 and season_data['REB'] is not None:
            season_data['RPG'] = round(season_data['REB'] / season_data['GP'], 1)
        else:
            season_data['RPG'] = 0

        # steals per game
        if season_data['GP'] > 0 and season_data['STL'] is not None:
            season_data['STLPG'] = round(season_data['STL'] / season_data['GP'], 1)
        else:
            season_data['STLPG'] = 0

        # Certain players (specifically from before 1980) don't have a 3pt %
        if season_data['FG3_PCT'] is None:
            season_data['FG3_PCT'] = 0

    # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player_headshot': player_headshot,
               'player_full_name': player_full_name,
               'player_stats': player_stats,
               'player_id': player_id,
               'player_bio': player_bio,
               #'player_awards': player_awards
               }

    return render(request, 'nba_stats/post_season.html', context=context)


# regular season rankings
def regular_season_rankings(request, player_full_name, player_id):
    # get session info containing player headshot, bio awards and career stats
    player_page_info = request.session.get("player_page_info", None)

    if player_page_info:
        player_headshot = player_page_info[0]
        player_bio = player_page_info[1]

        # get regular season stats
        career_stats = player_page_info[2]
        player_stats = career_stats['SeasonRankingsRegularSeason']

    else:
        # Get player headshot
        player_headshot = get_player_image(player_id, player_full_name)

        # Get regular season rankings
        player_stats = rankings_regular_season(player_id)

        # get player bio
        player_bio = get_player_bio(player_full_name)

    # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player_headshot': player_headshot,
               'player_full_name': player_full_name,
               'player_stats': player_stats,
               'player_id': player_id,
               'player_bio': player_bio,
               #'player_awards': player_awards
               }

    return render(request, 'nba_stats/regular_season_rankings.html', context=context)


# post season rankings
def post_season_rankings(request, player_full_name, player_id):
    # get session info containing player headshot, bio awards and career stats
    player_page_info = request.session.get("player_page_info", None)

    if player_page_info:
        player_headshot = player_page_info[0]
        player_bio = player_page_info[1]

        # get regular season stats
        career_stats = player_page_info[2]
        player_stats = career_stats['SeasonRankingsPostSeason']

    else:
        # Get player headshot
        player_headshot = get_player_image(player_id, player_full_name)

        # Get post season rankings
        player_stats = rankings_post_season(player_id)

        # get player bio
        player_bio = get_player_bio(player_full_name)

    # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player_headshot': player_headshot,
               'player_full_name': player_full_name,
               'player_stats': player_stats,
               'player_id': player_id,
               'player_bio': player_bio,
               #'player_awards': player_awards
               }

    return render(request, 'nba_stats/post_season_rankings.html', context=context)


# not used
def compare_players(request):
    if request.method == 'POST':
        form = PlayerCompareForm(request.POST)
        if form.is_valid():
            # Get the player name from the form's cleaned data
            player1 = form.cleaned_data['player1']
            player1.title()  # NBA API is case sensitive

            player2 = form.cleaned_data['player2']
            player2.title()

            # Use the NBA API to find the player's ID based on the name
            player1_info = players.find_players_by_full_name(player1)
            player2_info = players.find_players_by_full_name(player2)

            # Redirect to the search results page if both player are valid
            if player1_info and player2_info:
                player1_id = player1_info[0]['id']
                player1_full_name = player1_info[0]['full_name']

                player2_id = player2_info[0]['id']
                player2_full_name = player2_info[0]['full_name']

                # store players info into a list
                players_info = [player1_id, player2_id, player1_full_name, player2_full_name]

                # store players info in a session for use in next view
                request.session['players_info'] = players_info

                return redirect('nba_stats:compare_profiles')
            else:
                # If player not found, show an error message or handle it as needed
                # For simplicity, we'll just redirect back to the search form with an error message
                return redirect('nba_stats:compare_players')
    else:
        form = PlayerCompareForm()

        # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'form': form}

    return render(request, "nba_stats/compare_search.html", context)


# view for comparison home page
def compare_profiles(request, player1_full_name, player1_id, player2_full_name, player2_id):
    # get players info from session
    # players_info = request.session.get("player_info", None)
    player_compare_info = request.session.get('player_compare_info', None)  # info on 2 players from home page

    if player_compare_info:

        # Get player names
        player1_full_name = player_compare_info[2]
        player2_full_name = player_compare_info[3]

        # get players headshots
        player1_headshot, player1_bio, player1_id = fetch_player_data(player1_full_name)
        player2_headshot, player2_bio, player2_id = fetch_player_data(player2_full_name)

        del player1_bio['_state']  # to avoid TypeError
        del player2_bio['_state']  # to avoid TypeError

        player1_headshot = [player1_headshot.player_image_url, player1_headshot.background_colour]
        player2_headshot = [player2_headshot.player_image_url, player2_headshot.background_colour]

        # Get players yearly stats
        player1_career_stats = player_career_numbers(player1_id)
        player2_career_stats = player_career_numbers(player2_id)

        player1_stats = player1_career_stats['CareerTotalsRegularSeason']
        player2_stats = player2_career_stats['CareerTotalsRegularSeason']

        for season_data in player1_stats:

            # points per game
            if season_data['GP'] > 0 and season_data['PTS'] is not None:
                season_data['PPG'] = round(season_data['PTS'] / season_data['GP'], 2)
            else:
                season_data['PPG'] = 0  # To avoid division by zero in case GP is 0

            # assists per game
            if season_data['GP'] > 0 and season_data['AST'] is not None:
                season_data['APG'] = round(season_data['AST'] / season_data['GP'], 1)
            else:
                season_data['APG'] = 0

            # blocks per game
            if season_data['GP'] > 0 and season_data['BLK'] is not None:
                season_data['BLKPG'] = round(season_data['BLK'] / season_data['GP'], 1)
            else:
                season_data['BLKPG'] = 0

            # rebounds per game
            if season_data['GP'] > 0 and season_data['REB'] is not None:
                season_data['RPG'] = round(season_data['REB'] / season_data['GP'], 1)
            else:
                season_data['RPG'] = 0

            # steals per game
            if season_data['GP'] > 0 and season_data['STL'] is not None:
                season_data['STLPG'] = round(season_data['STL'] / season_data['GP'], 1)
            else:
                season_data['STLPG'] = 0

            # Certain players (specifically from before 1980) don't have a 3pt %
            if season_data['FG3_PCT'] is None:
                season_data['FG3_PCT'] = 0

        for season_data in player2_stats:

            # points per game
            if season_data['GP'] > 0 and season_data['PTS'] is not None:
                season_data['PPG'] = round(season_data['PTS'] / season_data['GP'], 2)
            else:
                season_data['PPG'] = 0  # To avoid division by zero in case GP is 0

            # assists per game
            if season_data['GP'] > 0 and season_data['AST'] is not None:
                season_data['APG'] = round(season_data['AST'] / season_data['GP'], 1)
            else:
                season_data['APG'] = 0

            # blocks per game
            if season_data['GP'] > 0 and season_data['BLK'] is not None:
                season_data['BLKPG'] = round(season_data['BLK'] / season_data['GP'], 1)
            else:
                season_data['BLKPG'] = 0

            # rebounds per game
            if season_data['GP'] > 0 and season_data['REB'] is not None:
                season_data['RPG'] = round(season_data['REB'] / season_data['GP'], 1)
            else:
                season_data['RPG'] = 0

            # steals per game
            if season_data['GP'] > 0 and season_data['STL'] is not None:
                season_data['STLPG'] = round(season_data['STL'] / season_data['GP'], 1)
            else:
                season_data['STLPG'] = 0

            # Certain players (specifically from before 1980) don't have a 3pt %
            if season_data['FG3_PCT'] is None:
                season_data['FG3_PCT'] = 0

    # stats dropdown form
    form = StatsCompForm()

    if request.method == 'POST':
        form = StatsCompForm(request.POST)

        # get selected option
        if form.is_valid():
            comp_option = form.cleaned_data['option']
            title = form.get_graph_title(comp_option)
            graph_data, stat = get_graph(player1_id, player1_full_name, player2_id, player2_full_name, comp_option, title)

            # Append graph and stat to players info list and store in session for use in next view
            # This list will hold all the info we need for the comparison view
            comparison_info = [player1_id, player2_id, player1_headshot, player2_headshot, player1_full_name,
                               player2_full_name, graph_data, player1_bio, player2_bio, stat]
            request.session['comparison_info'] = comparison_info
            return redirect('nba_stats:show_graph', player1_full_name=player1_full_name, player1_id=player1_id,
                            player2_full_name=player2_full_name, player2_id=player2_id)

        else:
            return redirect('nba_stats:compare_players')

        # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player1_headshot': player1_headshot,
               'player1_bio': player1_bio,
               'player2_bio': player2_bio,
               'player2_headshot': player2_headshot,
               'player1_full_name': player1_full_name,
               'player2_full_name': player2_full_name,
               'player1_stats': player1_stats,
               'player2_stats': player2_stats,
               'player1_id': player1_id,
               'player2_id': player2_id,
               'form': form
               }

    return render(request, "nba_stats/comparison.html", context)


# This view will show the comparison graph for the two players
def show_graph(request, player1_full_name, player1_id, player2_full_name, player2_id):
    # Get players
    comparison_info = request.session.get('comparison_info')

    # get player IDs
    player1_id = comparison_info[0]
    player2_id = comparison_info[1]

    # get players headshots
    player1_headshot = comparison_info[2]
    player2_headshot = comparison_info[3]

    # Get player names
    player1_full_name = comparison_info[4]
    player2_full_name = comparison_info[5]

    # get player bios
    player1_bio = comparison_info[7]
    player2_bio = comparison_info[8]

    # Get graph
    graph_data = comparison_info[6]

    # get stat comparison
    stat = comparison_info[9]


    # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player1_headshot': player1_headshot,
               'player2_headshot': player2_headshot,
               'player1_full_name': player1_full_name,
               'player2_full_name': player2_full_name,
               'graph_data': json.dumps(graph_data),
               'player1_id': player1_id,
               'player2_id': player2_id,
               'player1_bio': player1_bio,
               'player2_bio': player2_bio,
               'stat': stat
               }

    return render(request, "nba_stats/graph_comparison.html", context)


def player_graph(request, player_full_name, player_id, category):
    # get session info containing player headshot, bio awards and career stats
    player_page_info = request.session.get("player_page_info", None)

    if player_page_info:
        player_headshot = player_page_info[0]
        player_bio = player_page_info[1]
        graph_data = player_page_info[3]
        stat = player_page_info[4]

    # Initialize forms
    player_form = PlayerSearchForm()

    context = {'player_form': player_form,
               'player_headshot': player_headshot,
               'player_full_name': player_full_name,
               'player_bio': player_bio,
               'graph_data': json.dumps(graph_data),
               'player_id': player_id,
               'category': category,
               'stat': stat
               }

    return render(request, "nba_stats/player_graph.html", context=context)

def update_player_awards(request, player_id, player_name):
    # Check if league leaders already exist for today
    today = timezone.now().date()
    player_awards_data = CareerAwards.objects.filter(player_id=player_id).first()

    # check if award data already exists
    if player_awards_data:
        player_awards = player_awards_data.accomplishments
    else:
        # update the player awards and date
        player_awards = get_accolades(player_id)

        player_awards_instance = CareerAwards.objects.create(
            player_id=player_id,
            player_name=player_name,
            accomplishments=player_awards,
            date=today
        )
        player_awards_instance.save()

    context = {
        "player_awards": player_awards,
        "player_id": player_id,
        "player_name": player_name
    }

    return render(request, 'partials/player_awards.html', context=context)


def update_player_bio(request, player_id, player_name):
    # Check if player bio has been updated today
    today = timezone.now().date()
    player_bio_data = PlayerBio.objects.filter(player_id=player_id).first()

    if player_bio_data.date == today:
        player_bio = player_bio_data.__dict__
        del player_bio['_state']
    else:
        # get updated data and save
        player_bio = get_player_bio(player_id)

        player_bio_data.school = player_bio.get('education', '')
        player_bio_data.country = player_bio.player_bio.get('country', '')
        player_bio_data.height = player_bio.player_bio.get('height', '')
        player_bio_data.weight = player_bio.get('weight', '')
        player_bio_data.year = player_bio.get('year', '')
        player_bio_data.number = player_bio.get('number', '')
        player_bio_data.position = player_bio.get('position', '')
        player_bio_data.team_id = player_bio.get('team_id', '')
        player_bio_data.team_name = player_bio.get('team_name', '')
        player_bio_data.status = player_bio.get('status', '')
        player_bio_data.PTS = player_bio.get('PTS', 0)
        player_bio_data.REB = player_bio.get('REB', 0)
        player_bio_data.AST = player_bio.get('AST', 0)
        player_bio_data.BLK = player_bio.get('BLK', 0)
        player_bio_data.STL = player_bio.get('STL', 0)

        # save updated data
        player_bio_data.save()

    context = {
        'player_name': player_name,
        'player_bio': player_bio
    }

    return render(request, 'partials/player_bio.html', context=context)