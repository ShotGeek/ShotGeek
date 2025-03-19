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


# career stats
def player_career_numbers(player_id):
    # Construct the proxy URL
    has_proxy = False

    try:
        if SMARTPROXY_USERNAME is None or SMARTPROXY_PASSWORD is None:
            raise ValueError("Proxy credentials are missing. Cannot create a valid proxy URL.")

        proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"
        has_proxy = True

    except ValueError as e:
        print(f"Error: {e}")
        has_proxy = False

    if has_proxy:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    else:
        player_stats = playercareerstats.PlayerCareerStats(player_id=player_id)

    # Get the player's career stats as a dictionary
    career_dict = player_stats.get_normalized_dict()

    return career_dict


# regular season totals
def player_regular_season(player_id):
    # Construct the proxy URL
    proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"

    player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    regular_season_totals = dict_response['SeasonTotalsRegularSeason']

    return regular_season_totals


# playoff totals
def player_post_season(player_id):
    # Construct the proxy URL
    proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"

    player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    post_season_totals = dict_response['SeasonTotalsPostSeason']

    return post_season_totals


def rankings_regular_season(player_id):
    # Construct the proxy URL
    proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"

    player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    regular_season_rankings = dict_response['SeasonRankingsRegularSeason']

    return regular_season_rankings


def rankings_post_season(player_id):
    # Construct the proxy URL
    proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"

    player_stats = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
    dict_response = player_stats.get_normalized_dict()  # Getting dictionary response

    post_season_rankings = dict_response['SeasonRankingsPostSeason']

    return post_season_rankings


# retrieving player headshot and team id
def get_player_image(player_id):
    # Construct the proxy URL
    proxy_url = f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"

    # get player's team id
    player_info = commonplayerinfo.CommonPlayerInfo(player_id, proxy=proxy_url)
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


# def get_player_image2(player_id, player_name):
#     # get player info
#     player_info = commonplayerinfo.CommonPlayerInfo(player_id)
#     player_bio = player_info.get_dict()
#     player_data = player_bio['resultSets'][0]['rowSet'][0]
#     team_id = int(player_data[18])
#
#     # Check for player image and team colour
#     player = PlayerHeadshot.objects.filter(player_id=player_id).first()
#     team_logo = TeamLogo.objects.filter(team_id=team_id).first()
#
#     if player and team_logo:
#         return player.head_shot_url, team_logo.team_colour
#
#     else:
#
#         url = f'https://www.nba.com/player/{player_id}'
#
#         # Make an HTTP GET request to the URL
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
#
#         # Parse the HTML content using BeautifulSoup
#         soup = BeautifulSoup(response.content, 'html.parser')
#
#         # Find the player image tag within the appropriate class or element
#         player_image_div = soup.find('div', {'class': 'PlayerSummary_mainInnerTeam____nFZ'})
#         if player_image_div:
#             img_tag = player_image_div.find('img',
#                                             {'class': 'PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif'})
#
#             if img_tag:
#                 head_shot_url = img_tag['src']
#
#                 # save image to database
#                 instance = PlayerHeadshot(player_id=player_id, player_name=player_name, head_shot_url=head_shot_url)
#                 instance.save()
#                 return head_shot_url, team_logo.team_colour
#
#     return None


# function for getting player graph
def get_graph(player1_id, player1_name, player2_id, player2_name, stat_category, title):
    # Get players yearly stats
    player1_stats = player_regular_season(player1_id)
    player2_stats = player_regular_season(player2_id)

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

    #  We need to find which player has had the the shorter season between the two
    # The shorter season will be used to plot the x axis
    if len(player1_stats) > len(player2_stats):
        seasons = len(player2_stats)
        longer_player = player1_name
        tenure = len(player1_stats)

    else:
        seasons = len(player1_stats)
        longer_player = player2_name
        tenure = len(player2_stats)

    # Extract stat category we are comparing for both players
    player1_numbers = [player1_stats[i][stat_category] for i in range(seasons)]
    player2_numbers = [player2_stats[i][stat_category] for i in range(seasons)]

    # Create a line chart using Matplotlib
    plt.figure(figsize=(10, 6))

    # plot both line graphs
    # x-axis values to range(1, seasons + 1) to match the length of player1_numbers and player2_numbers.
    plt.plot(range(1, seasons + 1), player1_numbers, label=player1_name, marker='o')
    plt.plot(range(1, seasons + 1), player2_numbers, label=player2_name, marker='o')

    # Chart labels
    plt.title(f'{player1_name} and {player2_name} {title} Comparison')
    plt.xlabel('Seasons')
    plt.ylabel(title)
    plt.legend()
    plt.grid(True)

    # Set x-axis ticks to be integer values only
    # The plt.xticks function is used to set the x-axis ticks, and it expects a 1D array-like iterable input
    plt.xticks(range(1, seasons + 1))

    # Save the plot to a BytesIO object
    img_data = BytesIO()
    plt.savefig(img_data, format='png')
    plt.close()

    # Move the buffer's position to the start
    img_data.seek(0)
    encoded_image = base64.b64encode(img_data.read()).decode("utf-8")

    return encoded_image


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

    elif career_category == 'Post Season':
        player_stats = career_stats['SeasonTotalsPostSeason']
        graph_title = f"{player_name} Career Post Season {title} Stats"
        title = f"{title} Per Game"

        # getting per game averages
        for season_data in player_stats:

            # points per game
            if season_data['GP'] > 0:
                season_data['PPG'] = round(season_data['PTS'] / season_data['GP'], 2)
            else:
                season_data['PPG'] = 0  # To avoid division by zero in case GP is 0

            # assists per game
            if season_data['GP'] > 0:
                season_data['APG'] = round(season_data['AST'] / season_data['GP'], 1)
            else:
                season_data['APG'] = 0

            # blocks per game
            if season_data['GP'] > 0:
                season_data['BLKPG'] = round(season_data['BLK'] / season_data['GP'], 1)
            else:
                season_data['BLKPG'] = 0

            # rebounds per game
            if season_data['GP'] > 0:
                season_data['RPG'] = round(season_data['REB'] / season_data['GP'], 1)
            else:
                season_data['RPG'] = 0

            # steals per game
            if season_data['GP'] > 0:
                season_data['STLPG'] = round(season_data['STL'] / season_data['GP'], 1)
            else:
                season_data['STLPG'] = 0


    elif career_category == 'Reg. Season Rankings':
        player_stats = career_stats['SeasonRankingsRegularSeason']
        stat_category = rankings_map[stat_category]
        graph_title = f"{player_name} Career Regular Season {title} Rankings"
        title = f"{title} Ranking"


    elif career_category == 'Post Season Rankings':
        player_stats = career_stats['SeasonRankingsPostSeason']
        stat_category = rankings_map[stat_category]
        graph_title = f"{player_name} Career Post Season {title} Rankings"
        title = f"{title} Ranking"

    # x axis
    seasons = len(player_stats)

    # Extract stat category data
    player_numbers = [player_stats[i][stat_category] for i in range(seasons)]

    # Create a line chart using Matplotlib
    plt.figure(figsize=(10, 6))

    plt.plot(range(1, seasons + 1), player_numbers, label=player_name, marker='o')

    # Chart labels
    plt.title(f'{graph_title}')
    plt.xlabel(f'{career_category} Years')
    plt.ylabel(title)
    plt.legend()
    plt.grid(True)

    # Set x-axis ticks to be integer values only
    # The plt.xticks function is used to set the x-axis ticks, and it expects a 1D array-like iterable input
    plt.xticks(range(1, seasons + 1))

    # Save the plot to a BytesIO object
    img_data = BytesIO()
    plt.savefig(img_data, format='png')
    plt.close()

    # Move the buffer's position to the start
    img_data.seek(0)
    encoded_image = base64.b64encode(img_data.read()).decode("utf-8")

    return encoded_image
