from django.shortcuts import render, redirect
from django.contrib import messages
from nba_stats.forms import PlayerSearchForm
from nba_stats.models import *
from .functions import *
from nba_stats.functions import *
from .forms import PlayerOneForm, PlayerTwoForm
from nba_teams.models import *
from django.utils import timezone


def home(request):

    word_of_the_day = get_word_of_the_day()
    error_message = None
    player_form = PlayerSearchForm()
    player1_form = PlayerOneForm()
    player2_form = PlayerTwoForm()


    # Delete session data
    request.session.pop('player_page_info', None)
    request.session.pop('player_info', None)
    request.session.pop('player_compare_info', None)



    player_compare_info = []
    player1 = request.session.get('player1', "Lebron james")
    player2 = request.session.get('player2', 'Michael jordan')

    try:
        # Fetch player data
        player1_headshot, player1_bio, player1_id = fetch_player_data(player1)

        # player1 validation check
        if not player1_headshot or not player1_bio or not player1_id:
            raise ValueError("Player not found")

    except ValueError as e:
        request.session.pop('player1', None)
        messages.error(request, f"Could not find player '{player1}'. Please check your spelling and try again.")
        return redirect('home')
    
    try:
        # Fetch player data
        player2_headshot, player2_bio, player2_id = fetch_player_data(player2)

        # player2 validation check
        if not player2_headshot or not player2_bio or not player2_id:
            raise ValueError("Player not found")

    except ValueError as e:
        request.session.pop('player2', None)
        messages.error(request, f"Could not find player '{player2}'. Please check your spelling and try again.")
        return redirect('home')

    # Prepare player images
    player1_image = [player1_headshot.player_image_url, player1_headshot.background_colour]
    player2_image = [player2_headshot.player_image_url, player2_headshot.background_colour]

    # get player full name
    player1_fullname = player1_headshot.player_name
    player2_fullname = player2_headshot.player_name 

    eastern_teams = EasternConferenceTeams.objects.all()
    western_teams = WesternConferenceTeams.objects.all()

    # Add player 1 and player 2 data to session for comparison
    player_compare_info.extend([player1_id, player2_id, player1, player2])
    request.session['player_compare_info'] = player_compare_info

    if request.method == 'POST':
        try:
            # Handle the main search form
            player_form = PlayerSearchForm(request.POST)
            if player_form.is_valid():
                search_term = player_form.cleaned_data['player_name'].title()

                # Search for the team by name
                team_id = search_team_by_name(search_term, eastern_teams, western_teams)
                if team_id:
                    return redirect('nba_teams:team_page', team_id=team_id)

                # Search for the player data
                player_headshot, player_bio, player_id = fetch_player_data(search_term)
                if not player_headshot or not player1_bio or not player_id:
                    print("error caught")
                    messages.error(request, f"Could not find player '{search_term}'. Please check your spelling and try again.")
                    return redirect('home')

                player_full_name = player_headshot.player_name
                player_headshot = [player_headshot.player_image_url, player_headshot.background_colour]
                del player_bio['_state']  # to avoid TypeError

                request.session['player_info'] = [player_headshot, player_bio]

                return redirect('nba_stats:player_details', player_id=player_id, player_full_name=player_full_name)

            # Handle player1 and player2 search forms
            player1_form = PlayerOneForm(request.POST)
            player2_form = PlayerTwoForm(request.POST)
            if player1_form.is_valid():
                request.session['player1'] = player1_form.cleaned_data['player1_name'].title()
                return redirect('home')
            if player2_form.is_valid():
                request.session['player2'] = player2_form.cleaned_data['player2_name'].title()
                return redirect('home')

        except ValueError as e:
            context = {
                'message': "Player not found. Please check the spelling and try again."
            }
            return render(request, 'error.html', context)

    context = {
        'player_form': player_form,
        'player1_id': player1_id,
        'player2_id': player2_id,
        'player1_form': player1_form,
        'player2_form': player2_form,
        'player1_image': player1_image,
        'player2_image': player2_image,
        'player1': player1_fullname,
        'player2': player2_fullname,
        'player1_bio': player1_bio,
        'player2_bio': player2_bio,
        'error_message': error_message,
        'word_of_the_day': word_of_the_day
    }

    return render(request, "index.html", context=context)

def about(request):
    player_form = PlayerSearchForm()
    context = {
        'player_form': player_form,

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
