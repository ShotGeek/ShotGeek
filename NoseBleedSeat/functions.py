from nba_api.stats.static import players
from nba_api.stats.endpoints import playerawards, commonplayerinfo, leagueleaders
from nba_stats.models import *
from nba_stats.functions import *
from .constants import WORDS
from django.conf import settings
import random, time



def create_proxy_url():
    """Helper function to create the proxy URL."""
    if settings.SMARTPROXY_USERNAME and settings.SMARTPROXY_PASSWORD:
        proxy_url = f"http://{settings.SMARTPROXY_USERNAME}:{settings.SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"
        return proxy_url
    else:
        return None

def fetch_player_data(player_name, player_id=None):
    """Helper function to fetch or create player headshot and bio."""

    player_headshot = PlayerHeadShot.objects.filter(player_name=player_name).first()
    player_bio_data = PlayerBio.objects.filter(player_name=player_name).first()

    # check for player info using player name
    if player_id is None:
        player_info = players.find_players_by_full_name(player_name)

        # if player data is not found return none
        if not player_info:
            return None, None, None
        else:
            player_id = player_info[0]['id']
            player_name = player_info[0]['full_name']

    # one more check by player id
    player_headshot = PlayerHeadShot.objects.filter(player_id=player_id).first()
    if player_headshot:
        pass
    else:
        player_image = get_player_image(player_id)
        player_url = player_image[0]
        player_team_id = player_image[1]

        player_headshot = PlayerHeadShot.objects.create(
            player_id=player_id,
            player_name=player_name,
            player_image_url=player_url,
            team_id=player_team_id,
            background_colour=None
        )
        player_headshot.save()

    player_id = player_headshot.player_id
    player_name = player_headshot.player_name

    if not player_bio_data:

        # one more check by id
        player_bio_data = PlayerBio.objects.filter(player_id=player_id).first()
        if player_bio_data:
            pass

        else:
            player_bio = get_player_bio(player_id)
            player_bio_data = PlayerBio.objects.create(
                player_id=player_id,
                player_name=player_name,
                school=player_bio.get('education', ''),
                country=player_bio.get('country', ''),
                height=player_bio.get('height', ''),
                weight=player_bio.get('weight', ''),
                year=player_bio.get('year', ''),
                number=player_bio.get('number', ''),
                position=player_bio.get('position', ''),
                team_id=player_bio.get('team_id', ''),
                team_name=player_bio.get('team_name', ''),
                status=player_bio.get('status', ''),
                PTS=player_bio.get('PTS', 0),
                REB=player_bio.get('REB', 0),
                AST=player_bio.get('AST', 0),
                BLK=player_bio.get('BLK', 0),
                STL=player_bio.get('STL', 0),
            )
            player_bio_data.save()

    player_bio = player_bio_data.__dict__
    # player_bio['date'] = player_bio['date'].isoformat()  # to convert date object into string

    return player_headshot, player_bio, player_id

def search_team_by_name(search_term, eastern_teams, western_teams):
    """Helper function to search for a team by name in both conferences."""
    for team in eastern_teams:
        if search_term in [team.team_name, team.team_full_name, team.team_city, team.team_abbreviated]:
            return team.team_id

    for team in western_teams:
        if search_term in [team.team_name, team.team_full_name, team.team_city, team.team_abbreviated]:
            return team.team_id

    return None

def get_player_awards(player_name, player_id):
    awards_data = CareerAwards.objects.filter(player_id=player_id).first()

    if not awards_data:
        player_awards = get_accolades(player_id)
        awards_instance = CareerAwards.objects.create(
            player_id=player_id,
            player_name=player_name,
            accomplishments=player_awards
        )
        awards_instance.save()
    else:
        player_awards = awards_data.accomplishments

    return player_awards

def get_league_leaders():
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    stats = ["PTS", "BLK", "REB", "AST", "STL", "FGM", "FG3M", "FTM", "EFF", "AST_TOV", "STL_TOV"]

    # To map each key with a readable value
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

    stat_leaders = {}

    # get league leaders from database
    league_leaders_data = LeagueLeaders.objects.first()

    if league_leaders_data:
        leaders_data = league_leaders_data.leaders
        stat_leaders = leaders_data
    else:
        # Get the league leaders data from the external API
        for category in stats:

            # production with proxy
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
                        player_image_url=player_headshot[
                            0] if player_headshot else "https://static.vecteezy.com/system/resources/thumbnails/004/511/281/small_2x/default-avatar-photo-placeholder-profile-picture-vector.jpg",
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

    return stat_leaders

def get_per_game_stats(player_id):
        
    # Construct the proxy URL
    proxy_url = create_proxy_url()
    stats = []
    # production with proxy
    if proxy_url:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)

    career_dict = player_stats.get_normalized_dict()
    player_career_regular_season_totals = career_dict['CareerTotalsRegularSeason'][0]  # get career totals
    games_played = int(player_career_regular_season_totals['GP'])

    # points per game
    if player_career_regular_season_totals['PTS'] is not None:
        ppg = round(int(player_career_regular_season_totals['PTS']) / games_played, 1)
        stats.append(ppg)
    else:
        stats.append(0)

    # rebounds per game
    if player_career_regular_season_totals['REB'] is not None:
        reb = round(int(player_career_regular_season_totals['REB']) / games_played, 1)
        stats.append(reb)
    else:
        stats.append(0)

    # assists per game
    if player_career_regular_season_totals['AST'] is not None:
        assists = round(int(player_career_regular_season_totals['AST']) / games_played, 1)
        stats.append(assists)
    else:
        stats.append(0)

    # steals per game
    if player_career_regular_season_totals['STL'] is not None:
        steals = round(int(player_career_regular_season_totals['STL']) / games_played, 1)
        stats.append(steals)
    else:
        stats.append(0)

    # blocks per game
    if player_career_regular_season_totals['BLK'] is not None:
        blocks = round(int(player_career_regular_season_totals['BLK']) / games_played, 1)
        stats.append(blocks)
    else:
        stats.append(0)

    # years played
    years = len(career_dict['SeasonTotalsRegularSeason'])
    stats.append(years)

    return stats

def get_player_bio(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()
    bio = {}

    # get player info

    # production with proxy
    if proxy_url:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)

    player_bio = player_info.get_dict()

    # player stats
    per_game_stats = get_per_game_stats(player_id)
    bio['PTS'] = per_game_stats[0]  # points
    bio['REB'] = per_game_stats[1]  # rebounds
    bio['AST'] = per_game_stats[2]  # assists
    bio['STL'] = per_game_stats[3]  # steals
    bio['BLK'] = per_game_stats[4]  # blocks
    bio['year'] = per_game_stats[5]  # years played

    """
    This is how to get the current season's averages, will be useful for later updates
    player_stats = player_bio['resultSets'][1]['rowSet'][0]

    # points
    player_pts = player_stats[3]
    bio['PTS'] = player_pts

    # ast
    player_ast = player_stats[4]
    bio['AST'] = player_ast

    # reb
    player_reb = player_stats[5]
    bio['REB'] = player_reb
    """

    # player info
    player_data = player_bio['resultSets'][0]['rowSet'][0]

    # college / high school
    if player_data[8] == "":
        bio['education'] = "N/A"
    else:
        bio['education'] = player_data[8]

    # country
    if player_data[9] == "":
        bio['country'] = "N/A"
    else:
        bio['country'] = player_data[9]

    # height
    if player_data[11] == "":
        bio['height'] = 00.00
    else:
        bio['height'] = player_data[11]

    # weight
    if player_data[12] == "":
        bio['weight'] = 00.00
    else:
        bio['weight'] = player_data[12]

    # years
    # bio['year'] = player_data[13]

    # jersey number
    if player_data[14] == "":
        bio['number'] = 0
    else:
        bio['number'] = player_data[14]

    # position
    if player_data[15] == "":
        bio['position'] = "N/A"
    else:
        bio['position'] = player_data[15]

    # play status
    if player_data[16] == "":
        bio['status'] = "N/A"
    else:
        bio['status'] = player_data[16]

    # team
    if player_data[19] == "":
        bio['team'] = "N/A"
    else:
        bio['team'] = player_data[19]

    # team id
    if player_data[18] == "":
        bio['team_id'] = 1610612752  # putting Knicks as the default id so that players can have an orange background
    else:
        bio['team_id'] = int(player_data[18])

    return bio

def get_accolades(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()
    accolades = []
    accolades_history = {}

    # get list of accolades

    # production with proxy
    if proxy_url:
        player_accolades = playerawards.PlayerAwards(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_accolades = playerawards.PlayerAwards(player_id=player_id)

    # add award descriptions to accolades empty list
    player_awards = player_accolades.get_data_frames()[0]
    for info in player_awards['DESCRIPTION']:
        accolades.append(info)

    # sort list so that awards are organized alphabetically
    accolades.sort()

    # count how many times an award appears and map it to award
    count = 1
    for num, award in enumerate(accolades):
        if num + 1 < len(accolades) and award == accolades[num + 1]:
            count += 1
        else:
            accolades_history[award] = count
            count = 1

    return accolades_history


random.seed(time.time())

def get_word_of_the_day() -> str:
    return random.choice(WORDS)
