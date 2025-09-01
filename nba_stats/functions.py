import base64
import io
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo, PlayerGameLog, shotchartdetail
import requests
from bs4 import BeautifulSoup
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib import cm
from matplotlib.patches import Circle, Rectangle, Arc

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

        player2_numbers = [player2_stats[i].get(stat_category, 0) for i in range(seasons)] # fill longer player's stats
    
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

        player1_numbers = [player1_stats[i].get(stat_category, 0) for i in range(seasons)]

    #
    else:
        seasons = len(player1_stats)
        player1_numbers = [player1_stats[i].get(stat_category, 0) for i in range(seasons)]
        player2_numbers = [player2_stats[i].get(stat_category, 0) for i in range(seasons)]

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

def get_game_log(player_id, season, season_type):
      # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        game_log = PlayerGameLog(player_id=player_id, season=season, season_type_all_star=season_type, proxy=proxy_url)
        game_data = game_log.get_data_frames()[0]  # Get the first DataFrame from the list
    else:
        game_log = PlayerGameLog(player_id=player_id, season=season, season_type_all_star=season_type)
        game_data = game_log.get_data_frames()[0]

    # select and rename relevant columns
    game_data = game_data[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'PLUS_MINUS']]
    #game_data.columns = ['Date', 'Matchup', 'Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Minutes', 'FG Made', 'FG Attempted', 'FG Percentage', '3P Made', '3P Attempted', '3P%', 'FT Made', 'FT Attempted', 'FT%', 'Offensive Rebs', 'Defensive Rebs', 'Plus/Minus']

    return game_data

def get_shot_chart(player_id, team_id, season, season_type, context_measure):
    # Construct the proxy URL
    proxy_url = create_proxy_url()

    # production with proxy
    if proxy_url:
        shot_chart_list = shotchartdetail.ShotChartDetail(
            team_id=team_id,
            player_id=player_id,
            season_type_all_star=season_type,
            season_nullable=season,
            context_measure_simple=context_measure,
            proxy=proxy_url
        )
        shot_chart = shot_chart_list.get_data_frames()  
    else:
        shot_chart_list = shotchartdetail.ShotChartDetail(
            team_id=team_id,
            player_id=player_id,
            season_type_all_star=season_type,
            season_nullable=season,
            context_measure_simple=context_measure
        )
        shot_chart = shot_chart_list.get_data_frames()

    return shot_chart[0], shot_chart[1]  # Return the first two DataFrames (shot data and league averages)


# draw court function
def draw_court(ax=None, color="black", lw=1, outer_lines=False):

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 11))

    # Basketball Hoop
    hoop = Circle((0,0), radius=7.5, linewidth=lw, color=color, fill=False)

    # Backboard
    backboard = Rectangle((-30, -12.5), 60, 0, linewidth=lw, color=color)

    # The paint
    # outer box
    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False)
    # inner box
    inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False)

    # Free Throw Top Arc
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180, linewidth=lw, color=color, fill=False)

    # Free Bottom Top Arc
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color)

    # Restricted Zone
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw, color=color)

    # Three Point Line
    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw, color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)
    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw, color=color)

    # Center Court
    center_outer_arc = Arc((0, 422.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color)
    center_inner_arc = Arc((0, 422.5), 40, 40, theta1=180, theta2=0, linewidth=lw, color=color)

    # list of court shapes
    court_elements = [hoop, backboard, outer_box, inner_box, top_free_throw, bottom_free_throw, restricted, corner_three_a, corner_three_b, three_arc, center_outer_arc, center_inner_arc]

    #outer_lines=True
    if outer_lines:
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw, color=color, fill=False)
        court_elements.append(outer_lines)

    for element in court_elements:
        ax.add_patch(element)

def shot_chart(
    data,
    title="",
    color="b",
    xlim=(-250, 250),
    ylim=(-47.5, 422.5),
    line_color="black",
    court_color="white",
    court_lw=2,
    outer_lines=False,
    flip_court=False,
    gridsize=None,
    ax=None,
    despine=False
):
    import matplotlib.patches as mpatches

    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 11))

    # Set axes limits
    if not flip_court:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    else:
        ax.set_xlim(xlim[::-1])
        ax.set_ylim(ylim[::-1])

    ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
    #ax.set_title(title, fontsize=18)

    # Draw the court
    draw_court(ax, color=line_color, lw=court_lw, outer_lines=outer_lines)

    # Separate by made or missed
    x_missed = data[data['EVENT_TYPE'] == 'Missed Shot']['LOC_X']
    y_missed = data[data['EVENT_TYPE'] == 'Missed Shot']['LOC_Y']

    x_made = data[data['EVENT_TYPE'] == 'Made Shot']['LOC_X']
    y_made = data[data['EVENT_TYPE'] == 'Made Shot']['LOC_Y']

    # Plot shots with clearer distinction
    ax.scatter(
        x_missed, y_missed,
        c='red',
        marker='x',
        s=250,
        linewidths=3,
        label="Missed Shot"
    )
    ax.scatter(
        x_made, y_made,
        facecolors='none',
        edgecolors='green',
        marker='o',
        s=150,
        linewidths=2,
        label="Made Shot"
    )

    # Set spines
    for spine in ax.spines:
        ax.spines[spine].set_lw(court_lw)
        ax.spines[spine].set_color(line_color)

    if despine:
        for spine in ["top", "bottom", "right", "left"]:
            ax.spines[spine].set_visible(False)

    # Add a legend (key)
    ax.legend(loc="upper right", fontsize=12, frameon=True, facecolor="white")

    return ax


def render_plot_to_base64(fig=None, format="png"):
    """
    Save a Matplotlib figure to base64 so it can be embedded in templates.
    If no figure is passed, will use the current active figure.
    """
    buf = io.BytesIO()
    if fig is None:
        plt.savefig(buf, format=format, bbox_inches="tight")
        plt.close()
    else:
        fig.savefig(buf, format=format, bbox_inches="tight")
        plt.close(fig)

    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")