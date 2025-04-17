from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import requests
import os

# Proxy configuration
SMARTPROXY_URL = os.getenv('SMARTPROXY_URL')
SMARTPROXY_USERNAME = os.getenv('SMARTPROXY_USERNAME')
SMARTPROXY_PASSWORD = os.getenv('SMARTPROXY_PASSWORD')

def create_proxy_url():
    """Helper function to create the proxy URL."""
    if SMARTPROXY_USERNAME and SMARTPROXY_PASSWORD:
        proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"
        return proxy_url
    else:
        return None

# career stats
def player_career_numbers(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)

    # Get the player's career stats as a dictionary
    career_dict = player_stats.get_normalized_dict()

    return career_dict


# regular season totals
def player_regular_season(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    
    
    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    regular_season_totals = dict_response['SeasonTotalsRegularSeason']

    return regular_season_totals


# playoff totals
def player_post_season(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)

    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    post_season_totals = dict_response['SeasonTotalsPostSeason']

    return post_season_totals


def rankings_regular_season(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)

    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    regular_season_rankings = dict_response['SeasonRankingsRegularSeason']

    return regular_season_rankings


def rankings_post_season(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    
    
    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    post_season_rankings = dict_response['SeasonRankingsPostSeason']

    return post_season_rankings


# retrieving player headshot and team id
def get_player_image(player_id):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # get player's team id

    # production with proxy
    if proxy_url:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id, proxy=proxy_url)
    # development without proxy
    else:
        player_info = commonplayerinfo.CommonPlayerInfo(player_id)
    
    
    player_bio = player_info.get_dict()
    player_data = player_bio['resultSets'][0]['rowSet'][0]
    team_id = int(player_data[18])

    # begin scrapping for image url
    url = f'https://www.nba.com/player/{player_id}'

    # Make an HTTP GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the player image tag within the appropriate class or element
    player_image_div = soup.find('div', {'class': 'PlayerSummary_mainInnerTeam____nFZ'})
    if player_image_div:
        img_tag = player_image_div.find('img',
                                        {'class': 'PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif'})

        if img_tag:
            head_shot_url = img_tag['src']
            return head_shot_url, team_id

    return None


# function for getting comparison graph
def get_graph(player1_id, player1_name, player2_id, player2_name, stat_category, title):
    # Get players yearly stats
    player1_stats = player_regular_season(player1_id)
    player2_stats = player_regular_season(player2_id)

    # get player 1 per game stats
    player1_stats = regular_season_per_game_stats(player1_stats)
    # get player 1 percentage stats
    player1_stats = get_percentage_stats(player1_stats)

    # get player 2 per game stats
    player2_stats = regular_season_per_game_stats(player2_stats)
    # get player 2 percentage stats
    player2_stats = get_percentage_stats(player2_stats)

    # check if the players have played the same number of seasons
    if len(player1_stats) < len(player2_stats):
        seasons = len(player2_stats) # Use the longer player's seasons
        player1_numbers = []

        # Fill in the missing seasons stats for player1 with 0s
        # This is done to ensure that the x axis is the same for both players
        for i in range(seasons):
            try:
                player1_numbers.append(player1_stats[i][stat_category])
            except IndexError:
                player1_numbers.append(0)  # Entire season is missing
            except KeyError:
                player1_numbers.append(0)  # Stat missing in this season

        player2_numbers = [player2_stats[i][stat_category] for i in range(seasons)] # fill longer player's stats
    
    elif len(player2_stats) < len(player1_stats):
        seasons = len(player1_stats)
        player2_numbers = []
        for i in range(seasons):
            try:
                player2_numbers.append(player2_stats[i][stat_category])
            except IndexError:
                player2_numbers.append(0)
            except KeyError:
                player2_numbers.append(0)

        player1_numbers = [player1_stats[i][stat_category] for i in range(seasons)]

    #
    else:
        seasons = len(player1_stats)
        player1_numbers = [player1_stats[i][stat_category] for i in range(seasons)]
        player2_numbers = [player2_stats[i][stat_category] for i in range(seasons)]

    # Prepare data for Chart.js
    labels = [f"Season {i+1}" for i in range(seasons)]
    data = {
        "labels": labels,
        "datasets": [
            {
                "label": player1_name,
                "data": player1_numbers,
                "borderColor": "#000000",
                "backgroundColor": "rgba(255, 253, 208, 0.50)",
                "fill": True
            },
            {
                "label": player2_name,
                "data": player2_numbers,
                "borderColor": "#b4513e",
                "backgroundColor": "rgba(241, 84, 58, 0.50)",
                "fill": True
            }
        ]
    }
    return data,title  # return the chart data and the stat category being compared

# function to get individual player graph
def get_player_graph(player_id, player_name, career_stats, stat_category, career_category, title):
    rankings_map = {
        'PPG': 'RANK_PTS',
        'RPG': 'RANK_REB',
        'APG': 'RANK_AST',
        'BLKPG': 'RANK_BLK',
        'STLPG': 'RANK_STL',
        'FG_PCT': 'RANK_FG_PCT',
        'FG3_PCT': 'RANK_FG3_PCT',
        'FT_PCT': 'RANK_FT_PCT',
        'EFF': 'RANK_EFF'
    }

    # Get players yearly stats
    if career_category == 'Reg. Season':
        player_stats = career_stats['SeasonTotalsRegularSeason']
        graph_title = f"{player_name} Career Regular Season {title} Stats"
        title = f"{title} Per Game"
        # get years played for x axis
        years_played = get_years_played(player_stats)
        # getting per game averages
        player_stats = regular_season_per_game_stats(player_stats)
        # getting percentage stats
        player_stats = get_percentage_stats(player_stats)

        
    elif career_category == 'Post Season':
        player_stats = career_stats['SeasonTotalsPostSeason']
        graph_title = f"{player_name} Career Post Season {title} Stats"
        title = f"{title} Per Game"
        # get years played for x axis
        years_played = get_years_played(player_stats)
        # getting per game averages
        player_stats = post_season_per_game_stats(player_stats)
        # getting percentage stats
        player_stats = get_percentage_stats(player_stats)
    
    elif career_category == 'Reg. Season Rankings':
        player_stats = career_stats['SeasonRankingsRegularSeason']
        stat_category = rankings_map[stat_category]
        graph_title = f"{player_name} Career Regular Season {title} Rankings"
        title = f"{title} Ranking"
        # get years played for x axis
        years_played = get_years_played(player_stats)


    elif career_category == 'Post Season Rankings':
        player_stats = career_stats['SeasonRankingsPostSeason']
        stat_category = rankings_map[stat_category]
        graph_title = f"{player_name} Career Post Season {title} Rankings"
        title = f"{title} Ranking"
        # get years played for x axis
        years_played = get_years_played(player_stats)

     # x axis
    seasons = len(years_played) #len(player_stats)
    # Extract stat category data
    player_numbers = [player_stats[i][stat_category] for i in range(seasons)]

        # Prepare data for Chart.js
    labels = [f"{i}" for i in years_played]
    data = {
        "labels": labels,
        "datasets": [
            {
                "label": player_name,
                "data": player_numbers,
                "borderColor": "#b4513e",
                "backgroundColor": "rgba(241, 84, 58, 0.50)",
                "fill": True
            },
        ]}

    return data, graph_title  # return the chart data and the stat category being compared

# function to get player stats per game
def regular_season_per_game_stats(player_stats):
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

    return player_stats

# function to get post season per game stats
def post_season_per_game_stats(player_stats):
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

    return player_stats

# function to get percentage stats
def get_percentage_stats(player_stats):
    for season_data in player_stats:

        # certain players (specifically from before 1980) don't have a 3pt and other stats%

        if season_data['FG_PCT'] is not None:
            season_data['FG_PCT'] = round(season_data['FG_PCT'] * 100, 2)
        else:
            season_data['FG_PCT'] = 0
        if season_data['FG3_PCT'] is not None:
            season_data['FG3_PCT'] = round(season_data['FG3_PCT'] * 100, 2)
        else:
            season_data['FG3_PCT'] = 0
        if season_data['FT_PCT'] is not None:
            season_data['FT_PCT'] = round(season_data['FT_PCT'] * 100, 2)
        else:
            season_data['FT_PCT'] = 0

    return player_stats

# function to get the years played by a player
def get_years_played(player_stats):
    years_played = []
    for season_data in player_stats:
        year = season_data['SEASON_ID']
        if year not in years_played:
            years_played.append(year)
    return years_played