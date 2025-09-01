from django import template
from nba_teams.models import EasternConferenceTeams, WesternConferenceTeams

historical_teams = {
    "SEA": "https://sportslogohistory.com/wp-content/uploads/2017/12/seattle_supersonics_2002-2008.png",  # Seattle Supersonics
    "NJN": "https://sportslogohistory.com/wp-content/uploads/2016/SLH/nba_primary/new_jersey_nets.png", # New Jersey Nets
    "NOH": "https://sportslogohistory.com/wp-content/uploads/2017/12/new_orleans_hornets_2009-2013.png", # New Orleans Hornets
    "PHIL": "https://sportslogohistory.com/wp-content/uploads/2016/SLH/nba_primary/philadelphia_76ers_1978-1997.png", # Philadelphia 76ers
}

register = template.Library()


@register.filter
def percentage(value):
    if value in (None, ''):
        return ''
    if isinstance(value, str):
        value = float(value)
    return format(value, ".1%")

@register.filter
def team_logo(abbreviation):
    team = (EasternConferenceTeams.objects.filter(team_abbreviated=abbreviation).first() or
            WesternConferenceTeams.objects.filter(team_abbreviated=abbreviation).first())
    if team:
        return team.team_logo_url
    return ""  # or a default logo URL  

# this function is used for getting team logos in matchup_logos function
def get_logo(abbr):
    team = (EasternConferenceTeams.objects.filter(team_abbreviated=abbr).first() or
            WesternConferenceTeams.objects.filter(team_abbreviated=abbr).first())
    
    if team:
        return team.team_logo_url
    elif abbr in historical_teams:
        return historical_teams[abbr]
    else:
        ""

@register.filter
def matchup_logos(matchup):
    # Example: "CLE @ PHI" or "CLE vs. PHI"
    if not matchup:
        return ""
    parts = matchup.replace('vs.', '@').split('@')
    if len(parts) == 2:
        team1 = parts[0].strip()
        team2 = parts[1].strip()
        logo1 = get_logo(team1)
        logo2 = get_logo(team2)
        # Return HTML for both logos, inline and vertically centered
        return f'<span style="display:inline-flex;align-items:center;"><img src="{logo1}" alt="{team1} logo" height="50" style="vertical-align:middle; margin-right:4px;"/>@<img src="{logo2}" alt="{team2} logo" height="50" style="vertical-align:middle; margin-left:4px;"/></span>'
    return matchup
matchup_logos.is_safe = True  # Mark as safe for HTML
