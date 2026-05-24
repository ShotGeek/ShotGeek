from nba_api.stats.static import players
from nba_api.stats.endpoints import (
    playerawards, 
    commonplayerinfo, 
    leagueleaders, 
    playercareerstats,
)
from nba_stats.models import Player, PlayerBio, CareerAwards, LeagueLeaders, TEAM_COLOURS, PlayerStats
from nba_stats.functions import get_player_image
from .constants import WORDS
from django.conf import settings
import random
import time



NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

def create_proxy_url():
    """Helper function to create the proxy URL."""
    if settings.SMARTPROXY_USERNAME and settings.SMARTPROXY_PASSWORD:
        proxy_url = f"http://{settings.SMARTPROXY_USERNAME}:{settings.SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"
        return proxy_url
    else:
        return None
    
# new functions
def save_player_bio(player_name, player_id=None):
    # Get player_id from name if not provided (e.g. from a search query)
    if player_id is None:
        matches = players.find_players_by_full_name(player_name)
        if not matches:
            return None
        player_id = matches[0]['id']
        player_name = matches[0]['full_name']


    # Get or create the Player record so we can use it as a FK
    image_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
    player_obj, _ = Player.objects.get_or_create(
        player_id=player_id,
        defaults={'full_name': player_name, 'image_url': image_url, 'status': 'Active'},
    )

    # Skip if both records already exist
    if PlayerBio.objects.filter(player=player_obj).exists() and PlayerStats.objects.filter(player=player_obj).exists():
        return True

    proxy_url = create_proxy_url()

    for attempt in range(1, 4):
        try:
            time.sleep(random.uniform(1, 3) * attempt)  # stagger requests to avoid rate limiting
            # ── Create Bio (commonplayerinfo) ────────────────────────
            if proxy_url:
                print("we've got a proxy!")
                info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, proxy=proxy_url)
            else:
                print("No proxy!")
                info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, headers=NBA_HEADERS, timeout=60)

            result = info.get_dict()['resultSets'][0]
            data = result['rowSet'][0]
            headers = result['headers']

            def get(field):
                return data[headers.index(field)] if field in headers else None

            PlayerBio.objects.update_or_create(
                player=player_obj,
                defaults={
                    'team': get('TEAM_NAME') or '',
                    'position': (get('POSITION') or '')[:2],
                    'school': get('SCHOOL') or '',
                    'country': get('COUNTRY') or '',
                    'height': get('HEIGHT') or '',
                    'weight': float(get('WEIGHT') or 0) or None,
                    'year': get('DRAFT_YEAR') or None,
                    'years_pro': int(get('SEASON_EXP') or 0) or None,
                    'number': int(get('JERSEY') or 0) or None,
                }
            )
            time.sleep(0.6)

            # ── Career stats (playercareerstats) ──────────────
            if proxy_url:
                career = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
            else:
                career = playercareerstats.PlayerCareerStats(player_id=player_id, headers=NBA_HEADERS, timeout=60)

            d = career.get_normalized_dict()

            # ── PlayerStats — career per-game averages ────────
            reg_totals = d.get('CareerTotalsRegularSeason', [])
            if reg_totals:
                t = reg_totals[0]
                gp = t['GP'] or 1
                PlayerStats.objects.update_or_create(
                    player=player_obj,
                    defaults={
                        'PTS': round(t['PTS'] / gp, 1),
                        'REB': round(t['REB'] / gp, 1),
                        'AST': round(t['AST'] / gp, 1),
                        'BLK': round(t['BLK'] / gp, 1),
                        'STL': round(t['STL'] / gp, 1),
                    }
                )
            return False

        except Exception as e:
            print(f"[save_player_bio] attempt {attempt}/3 failed for {player_name}: {e}")
            if attempt < 3:
                time.sleep(attempt * 10)

    return None

# old functions

def fetch_player_data(player_name, player_id=None):
    """Helper function to fetch or create player and bio."""

    player_bio_data = PlayerBio.objects.filter(player__full_name=player_name).first()

    # check for player info using player name
    if player_id is None:
        player_info = players.find_players_by_full_name(player_name)

        # if player data is not found return none
        if not player_info:
            return None, None, None
        else:
            player_id = player_info[0]['id']
            player_name = player_info[0]['full_name']

    # look up or create player by id
    player = Player.objects.filter(player_id=player_id).first()
    if not player:
        image_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
        player = Player.objects.create(
            player_id=player_id,
            full_name=player_name,
            image_url=image_url,
            status='Active',
        )

    player_id = player.player_id
    player_name = player.full_name

    if not player_bio_data:

        # one more check by player FK
        player_bio_data = PlayerBio.objects.filter(player_id=player_id).first()
        if not player_bio_data:
            player_bio = get_player_bio(player_id)
            player_bio_data = PlayerBio.objects.create(
                player=player,
                school=player_bio.get('education', ''),
                country=player_bio.get('country', ''),
                height=player_bio.get('height', ''),
                weight=player_bio.get('weight', ''),
                year=player_bio.get('year', ''),
                number=player_bio.get('number', ''),
                position=player_bio.get('position', ''),
                team=player_bio.get('team', ''),
            )
            player_bio_data.save()

    player_bio = player_bio_data.__dict__

    return player, player_bio, player_id

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
                leaders = leagueleaders.LeagueLeaders(stat_category_abbreviation=category, headers=NBA_HEADERS)

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

                # Get or create player
                player = Player.objects.filter(player_id=player_id).first()
                if not player:
                    image_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
                    player = Player.objects.create(
                        player_id=player_id,
                        full_name=player_name,
                        image_url=image_url,
                        status='Active',
                    )

                player_image = player.image_url
                team_colour = TEAM_COLOURS.get(player.team_id)

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
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, headers=NBA_HEADERS)

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
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, headers=NBA_HEADERS)

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
        player_accolades = playerawards.PlayerAwards(player_id=player_id, headers=NBA_HEADERS)

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
