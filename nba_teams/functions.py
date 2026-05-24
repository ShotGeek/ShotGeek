from nba_stats.models import Player, TEAM_COLOURS
from nba_stats.functions import get_player_image
from nba_api.stats.endpoints import teamdetails, commonteamroster, teaminfocommon
from nba_teams.models import EasternConferenceTeams, WesternConferenceTeams, RetiredPlayers
import os

# Proxy configuration
SMARTPROXY_URL = os.getenv('SMARTPROXY_URL')
SMARTPROXY_USERNAME = os.getenv('SMARTPROXY_USERNAME')
SMARTPROXY_PASSWORD = os.getenv('SMARTPROXY_PASSWORD')

NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

def create_proxy_url():
    if SMARTPROXY_USERNAME and SMARTPROXY_PASSWORD:
        return f"http://{SMARTPROXY_USERNAME}:{SMARTPROXY_PASSWORD}@gate.smartproxy.com:10001"
    return None


def get_team(team_id):
    team = EasternConferenceTeams.objects.filter(team_id=team_id).first()

    if team:
        return team.team_id, team.team_name, team.team_logo_url, team.team_city, team.team_colour, team.team_full_name, team.team_city
    else:
        team = WesternConferenceTeams.objects.filter(team_id=team_id).first()
        return team.team_id, team.team_name, team.team_logo_url, team.team_city, team.team_colour, team.team_full_name, team.team_city


def get_team_history(team_id):
    proxy_url = create_proxy_url()

    # this is the info we need
    team_specifics = ['HEADCOACH', 'ARENA']
    current_history = {}
    team_championships = {}

    # get dictionary of information
    if proxy_url:
        team_details = teamdetails.TeamDetails(team_id=team_id, proxy=proxy_url)
    else:
        team_details = teamdetails.TeamDetails(team_id=team_id, headers=NBA_HEADERS)
    team_details = team_details.get_dict()

    # team championships
    chips = team_details['resultSets'][3]['rowSet']

    # team coach and arena
    basic_info = team_details['resultSets'][0]['headers']
    team_info = team_details['resultSets'][0]['rowSet'][0]
    for item in team_specifics:
        info = basic_info.index(item)
        current_history[item] = team_info[info]

    for year, team in chips:
        team_championships[year] = [team]

    return current_history, team_championships


def retired_players(team_id, team_name):
    proxy_url = create_proxy_url()

    retired_team = RetiredPlayers.objects.filter(team_id=team_id).first()
    if retired_team:
        retired_guys = retired_team.players
        return retired_guys

    retired_info = ['PLAYERID', 'PLAYER', 'POSITION', 'JERSEY', 'SEASONSWITHTEAM']
    retired_guys = []  # will contain lists of players and their information

    if proxy_url:
        team_details = teamdetails.TeamDetails(team_id=team_id, proxy=proxy_url)
    else:
        team_details = teamdetails.TeamDetails(team_id=team_id, headers=NBA_HEADERS)
    team_details = team_details.get_dict()
    retired_headings = team_details['resultSets'][6]['headers']
    retired = team_details['resultSets'][7]['rowSet']
    count = 0

    while count < len(retired):
        player_info = []
        for item in retired_info:
            info = retired_headings.index(item)
            player_info.append(retired[count][info])

        retired_guys.append(player_info)
        count += 1

    retired_instance = RetiredPlayers.objects.create(
        team_id=team_id,
        team_name=team_name,
        players=retired_guys
    )
    retired_instance.save()

    return retired_guys


def get_team_roster(team_id):
    proxy_url = create_proxy_url()

    final_roster = []  # will contain lists of players and their information
    player_info = ['PLAYER_ID', 'PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE', 'EXP']  # also need player id
    if proxy_url:
        team_details = commonteamroster.CommonTeamRoster(team_id=team_id, proxy=proxy_url)
    else:
        team_details = commonteamroster.CommonTeamRoster(team_id=team_id, headers=NBA_HEADERS)
    team_roster = team_details.get_dict()
    roster_headings = team_roster['resultSets'][0]['headers']
    lakers_roster = team_roster['resultSets'][0]['rowSet']
    count = 0

    while count < len(lakers_roster):
        player_details = []
        for item in player_info:
            # PLAYERID
            # PLAYER - --> Jalen Hood-Schifino
            # NUM - --> 0
            # POSITION - --> G
            # HEIGHT - --> 6-5
            # WEIGHT - --> 215
            # AGE - --> 21.0
            # EXP ---> R
            info = roster_headings.index(item)
            player_details.append(lakers_roster[count][info])

        # append player headshot and team colour
        # get player id
        player_id = player_details[0]

        # get player name
        player_name = player_details[1]

        # get player image and team colour
        player = Player.objects.filter(player_id=player_id).first()

        if not player:
            image_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
            player = Player.objects.create(
                player_id=player_id,
                full_name=player_name,
                image_url=image_url,
                status='Active',
            )

        player_head_shot = player.image_url
        team_colour = TEAM_COLOURS.get(player.team_id)
        player_details.append(player_head_shot)
        player_details.append(team_colour)

        # append player details to final roster
        final_roster.append(player_details)
        count += 1

    return final_roster


def get_team_rankings(team_id):
    proxy_url = create_proxy_url()

    team_ranks = {}

    team_record = ['TEAM_CONFERENCE', 'TEAM_DIVISION', 'W', 'L']
    team_record_map = {
        'TEAM_CONFERENCE': 'Conference',
        'TEAM_DIVISION': 'Division',
        'W': 'Wins',
        'L': 'Losses'
    }

    team_rankings = ['PTS_RANK', 'PTS_PG', 'REB_RANK', 'REB_PG', 'AST_RANK', 'AST_PG', 'OPP_PTS_RANK', 'OPP_PTS_PG']
    rankings_map = {
        'PTS_RANK': 'Points Ranking',
        'PTS_PG': 'Team Points Per Game',
        'REB_RANK': 'Rebounds Ranking',
        'REB_PG': 'Team Rebounds Per Game',
        'AST_RANK': 'Assists Ranking',
        'AST_PG': 'Assists Per Game',
        'OPP_PTS_RANK': 'Opponents Points Ranking',
        'OPP_PTS_PG': 'Opponents Points Per Game',
    }

    if proxy_url:
        rankings = teaminfocommon.TeamInfoCommon(team_id=team_id, proxy=proxy_url)
    else:
        rankings = teaminfocommon.TeamInfoCommon(team_id=team_id, headers=NBA_HEADERS)
    rankings = rankings.get_dict()
    record_headings = rankings['resultSets'][0]['headers']
    record = rankings['resultSets'][0]['rowSet'][0]

    # team conferences & record
    for item in team_record:
        info = record_headings.index(item)
        item = team_record_map[item]
        team_ranks[item] = record[info]

    # team league rankings
    team_rankings_info = rankings['resultSets'][1]['rowSet'][0]
    team_rank_headings = rankings['resultSets'][1]['headers']
    for item in team_rankings:
        info = team_rank_headings.index(item)
        item = rankings_map[item]
        team_ranks[item] = team_rankings_info[info]

    return team_ranks
